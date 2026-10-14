"""Film agent: shot spec + current frame -> video clip. Backends are swappable:
  * MockFilm — no GPU; slow zoom on the current frame (lets the whole loop run anywhere)
  * HTTPFilm — calls inception.film_server (Wan 2.2 TI2V-5B via DiffSynth) on this machine
"""
from __future__ import annotations

import base64
import time
from pathlib import Path

import httpx
import imageio.v3 as iio
import numpy as np
from PIL import Image

from ..config import settings
from ..state import Session
from .prompt import ShotSpec


class FilmResult:
    def __init__(self, video_path: Path, last_frame_path: Path, seconds: float, backend: str):
        self.video_path, self.last_frame_path, self.seconds, self.backend = video_path, last_frame_path, seconds, backend


def extract_last_frame(video_path: Path, out_path: Path) -> Path:
    frames = iio.imread(video_path, plugin="pyav")
    Image.fromarray(frames[-1]).save(out_path)
    return out_path


class MockFilm:
    name = "mock"

    def generate(self, image_path: Path, spec: ShotSpec, out_path: Path, seed: int = 0) -> Path:
        img = Image.open(image_path).convert("RGB").resize((settings.video_width, settings.video_height))
        n = settings.video_frames
        frames = []
        w, h = img.size
        for i in range(n):
            z = 1.0 + 0.15 * i / max(1, n - 1)
            cw, ch = int(w / z), int(h / z)
            left, top = (w - cw) // 2, (h - ch) // 2
            frames.append(np.asarray(img.crop((left, top, left + cw, top + ch)).resize((w, h))))
        iio.imwrite(out_path, np.stack(frames), fps=settings.video_fps, codec="libx264", plugin="pyav")
        return out_path


class HTTPFilm:
    name = "wan-http"

    def __init__(self, url: str | None = None):
        self.url = (url or settings.film_server_url).rstrip("/")

    def generate(self, image_path: Path, spec: ShotSpec, out_path: Path, seed: int = 0) -> Path:
        payload = {
            "image_b64": base64.b64encode(Path(image_path).read_bytes()).decode(),
            "prompt": spec.prompt,
            "negative_prompt": spec.negative_prompt,
            "width": settings.video_width,
            "height": settings.video_height,
            "num_frames": settings.video_frames,
            "fps": settings.video_fps,
            "steps": settings.video_steps,
            "seed": seed,
            "out_path": str(out_path),
        }
        r = httpx.post(self.url + "/generate", json=payload, timeout=1800)
        r.raise_for_status()
        return Path(r.json()["video_path"])


def make_backend(kind: str | None = None):
    kind = kind or settings.film_backend
    return MockFilm() if kind == "mock" else HTTPFilm()


class FilmAgent:
    name = "film"

    def __init__(self, session: Session, backend=None):
        self.session = session
        self.backend = backend or make_backend()

    def run(self, image_path: Path, spec: ShotSpec, tag: str, seed: int = 0) -> FilmResult:
        t0 = time.time()
        out = self.session.clips / f"{tag}.mp4"
        self.backend.generate(image_path, spec, out, seed=seed)
        last = extract_last_frame(out, self.session.frames / f"{tag}_last.png")
        res = FilmResult(out, last, time.time() - t0, self.backend.name)
        self.session.log(self.name, "clip", path=str(out), seconds=round(res.seconds, 1), backend=self.backend.name, seed=seed)
        return res
