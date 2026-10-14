"""QC for a streaming display: cheap per-frame pixel statistics that gate what is shown (and
trigger a re-seed on collapse), plus an asynchronous VLM audit that only writes to the log.
"""
from __future__ import annotations

import statistics
import threading
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from ..config import settings
from ..llm import VLM
from ..state import Session


class Verdict(BaseModel):
    scene_continuity: int = Field(ge=0, le=10, description="10 = clearly the same place/lighting as the start frame")
    action_match: int = Field(ge=0, le=10, description="10 = all expected visible results clearly happen")
    artifact_free: int = Field(ge=0, le=10, description="10 = no melting, flicker, extra limbs, text, or incoherent geometry")
    reason: str


SYSTEM = """You are a strict QUALITY-CONTROL judge for AI-generated first-person video clips in an interactive story. You see the START FRAME followed by 4 frames sampled in order from the generated clip. Score 0-10 on each axis and explain in one sentence. Be literal: if the expected result is not visible, action_match must be low."""


def sharpness(frame: np.ndarray) -> float:
    g = frame.mean(axis=2)
    lap = g[1:-1, 1:-1] * -4 + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


class FrameQC:
    """Pixel-statistics gate. `check` is per frame (<1 ms); `drift` compares a chunk's sharpness
    against the rolling history (WorldRoamBench-style best-minus-worst)."""

    def __init__(self, history: int = 10):
        self.hist: deque[float] = deque(maxlen=history)

    @staticmethod
    def check(frame: np.ndarray) -> tuple[bool, str]:
        m, s = float(frame.mean()), float(frame.std())
        if m < 8:
            return False, f"black frame (mean {m:.1f})"
        if m > 247:
            return False, f"blown-out frame (mean {m:.1f})"
        if s < 4:
            return False, f"flat frame (std {s:.1f})"
        return True, "ok"

    def drift(self, frames: list[np.ndarray]) -> tuple[bool, str]:
        if not frames:
            return True, "empty"
        sh = sharpness(frames[-1])
        ok = True
        reason = f"sharpness {sh:.0f}"
        if len(self.hist) >= 5:
            med = statistics.median(self.hist)
            if sh < 0.3 * med:
                ok, reason = False, f"sharpness collapsed {sh:.0f} vs median {med:.0f}"
        self.hist.append(sh)
        return ok, reason

    def reset(self) -> None:
        self.hist.clear()


class VLMAudit:
    """Asynchronous judge: never blocks the stream; results go to events.jsonl."""

    def __init__(self, session: Session, vlm: VLM | None = None):
        self.session = session
        self.vlm = vlm if vlm is not None else VLM()
        self.enabled = settings.qc_enabled and self.vlm.available

    def submit(self, start_frame: np.ndarray, frames: list[np.ndarray], expected: list[str], tag: str) -> None:
        if not self.enabled or not frames:
            return
        threading.Thread(target=self._run, args=(start_frame, frames, expected, tag), daemon=True).start()

    def _run(self, start_frame, frames, expected, tag) -> None:
        try:
            paths: list[Path] = []
            p0 = self.session.frames / f"{tag}_start.jpg"
            Image.fromarray(start_frame).save(p0, quality=85)
            paths.append(p0)
            n = len(frames)
            for k in range(4):
                i = min(n - 1, int(n * k / 4 + n / 8))
                p = self.session.frames / f"{tag}_qc{k}.jpg"
                Image.fromarray(frames[i]).save(p, quality=85)
                paths.append(p)
            user = "EXPECTED VISIBLE RESULTS: " + "; ".join(expected) + "\nFirst image is the START FRAME; the next 4 are sampled from the clip in order."
            v = self.vlm.json(SYSTEM, user, paths, Verdict)
            score = 0.4 * v.scene_continuity + 0.35 * v.action_match + 0.25 * v.artifact_free
            self.session.log("qc", "vlm_audit", tag=tag, score=round(score, 2), **v.model_dump())
        except Exception as e:  # audit failure must never affect the game
            self.session.log("qc", "vlm_audit_error", tag=tag, error=str(e)[:300])
