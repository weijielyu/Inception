"""Game: wires GM + Memory + renderers + Display into the hybrid loop.

    text ──► GM (1 LLM call) ──► dice ──► Memory.commit ──► Clip renderer ──► Display.enqueue_clip
    keys ──► Display (AR walk)          plot commitments (wall clock) ──► same path as text
"""
from __future__ import annotations

import logging
import threading
import time
import uuid

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from .agents.display import DisplayAgent, Subscriber
from .agents.gm import GMAgent
from .agents.memory import MemoryAgent
from .agents.qc import VLMAudit
from .agents.writer import WriterAgent
from .config import settings
from .llm import LLM, VLM
from .renderers.base import ARWalkRenderer, ClipRenderer, Keys
from .state import Entity, Session

log = logging.getLogger("inception.game")


class ViewCaption(BaseModel):
    view: str = Field(description="one sentence, <=30 words: what is visible right now (setting, main objects, lighting, colours)")


class SceneCaption(BaseModel):
    description: str = Field(description="3-4 sentences: setting, notable objects, lighting, mood, as seen from the viewer's position")
    visible_objects: list[str]


def make_renderers(width: int, height: int, fps: int) -> tuple[ARWalkRenderer, ClipRenderer]:
    if settings.ar_renderer == "mock":
        from .renderers.mock import MockARWalk
        ar: ARWalkRenderer = MockARWalk(width, height, fps)
    else:
        from .renderers.matrixgame2 import MatrixGame2Walk
        ar = MatrixGame2Walk(width, height, fps)
    if settings.clip_renderer == "mock":
        from .renderers.mock import MockClip
        clip: ClipRenderer = MockClip(width, height, fps, latency_s=settings.mock_clip_latency_s)
    else:
        from .renderers.wan_clip import WanClip
        rs = tuple(int(v) for v in settings.clip_render_size.lower().split("x")) if settings.clip_render_size else None
        clip = WanClip(width, height, fps, render_size=rs)
    return ar, clip


class Game:
    def __init__(self, ar: ARWalkRenderer | None = None, clip: ClipRenderer | None = None,
                 llm: LLM | None = None, vlm: VLM | None = None, session_id: str | None = None):
        self.session_id = session_id or time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
        self.session = Session(settings.sessions_dir / self.session_id)
        self.llm = llm or LLM()
        self.vlm = vlm if vlm is not None else VLM()
        self.w, self.h, self.fps = settings.video_width, settings.video_height, settings.display_fps
        if ar is None or clip is None:
            ar, clip = make_renderers(self.w, self.h, self.fps)
        self.ar, self.clip = ar, clip
        s = self.session
        self.gm = GMAgent(self.llm, s)
        self.memory = MemoryAgent(self.llm, s)
        self.writer = WriterAgent(self.llm, s)
        self.audit = VLMAudit(s, self.vlm)
        self.display = DisplayAgent(s, ar, self.fps, key_release_s=settings.key_release_s,
                                    on_idle_needed=self._regen_idle, on_tick=self._tick)
        self.clip_lock = threading.Lock()      # one GPU clip pipeline → serialize
        self.view_cache: tuple[int, str] = (-1, "")   # (display.version, caption of that frame)
        self.view_inflight: dict[int, threading.Event] = {}
        self.view_lock = threading.Lock()
        self.action_lock = threading.Lock()    # one narrative action at a time
        self.action_n = 0
        self.started = False

    # ----------------------------------------------------------------- setup
    def start(self, image_path: str, user_premise: str = "", scene_text: str = "", tone: str = "calm exploration") -> str:
        img = Image.open(image_path).convert("RGB").resize((self.w, self.h))
        frame = np.asarray(img)
        seed_path = self.session.frames / "seed.png"
        img.save(seed_path)

        if scene_text:
            description, objects = scene_text, []
        elif self.vlm.available:
            try:
                cap = self.vlm.json("Describe this scene for a game designer. Be concrete and literal.",
                                    "Describe the scene in JSON with keys `description` (string) and `visible_objects` (list of strings).",
                                    [seed_path], SceneCaption)
                description, objects = cap.description, cap.visible_objects
            except Exception as e:  # a flaky judge must not block world creation
                self.session.log("vlm", "scene_caption_error", error=str(e)[:300])
                description, objects = user_premise or "an outdoor first-person scene", []
        else:
            description, objects = user_premise or "an outdoor scene", []
        self.session.log("vlm", "scene_caption", description=description, objects=objects)

        setup = self.writer.setup(description, user_premise, tone)
        with self.session.lock:
            st = self.session.state
            st.scene.description, st.scene.style = description, setup.style
            st.scene.location, st.scene.time_of_day = setup.location, setup.time_of_day
            st.premise = setup.premise
            st.entities = [Entity(name=o, kind="object", state="as seen", where="in view") for o in objects]
            st.facts = [f"[hidden truth] {h}" for h in setup.hidden_truths]
            st.commitments = setup.commitments
            st.started_at = time.time()
            self.session.save()
        opening = self.llm.text(
            f"You are the narrator of a first-person adventure. Write 3 sentences in {settings.narration_lang}, second person present tense, placing the player in the scene with a hint of the premise. No questions, no menus.",
            f"SCENE: {description}\nPREMISE: {setup.premise}",
        )
        self.memory.record_turn("(start)", "scene established", opening)
        self.session.log("writer", "opening", text=opening)
        self.display.start(frame)   # also requests the first idle loop
        self.started = True
        self.display.event({"type": "narration", "text": opening, "tag": "opening"})
        self._push_state()
        return opening

    # ----------------------------------------------------------------- inputs
    def set_keys(self, keys: Keys) -> None:
        self.display.set_keys(keys)

    def subscribe(self, sub: Subscriber) -> None:
        self.display.subscribe(sub)

    def act(self, text: str) -> None:
        """Non-blocking: runs the narrative pipeline in a worker thread."""
        threading.Thread(target=self._do_action, args=(text, False), daemon=True, name="action").start()

    # --------------------------------------------------------------- pipeline
    def _do_action(self, text: str, plot: bool) -> None:
        with self.action_lock:
            self.action_n += 1
            n = self.action_n
            tag = f"{'plot' if plot else 'act'}{n:03d}"
            t0 = time.time()
            if not plot:
                self.display.last_input_t = time.time()
            self.display.lock_keys(True)
            self.display.event({"type": "status", "text": "…" if plot else f"You try: {text}", "tag": tag})
            try:
                view = self._caption_view(self.display.current_frame, self.display.version)
                res = self.gm.run(text, plot_event=plot, current_view=view)
                success, roll = self.gm.roll(res, n)
                branch = res.success if success else res.failure
                t_llm = time.time() - t0
                notes = self.memory.commit(branch.delta)
                self.memory.record_turn(text, branch.visible_result, branch.narration)
                self.display.event({"type": "narration", "text": branch.narration, "tag": tag, "kind": res.kind,
                                    "ruling": res.ruling, "success": success, "roll": roll, "reason": res.reason})
                self._push_state()
                if res.kind == "question":          # answered in words; the world keeps playing
                    self.display.lock_keys(False)
                    self.session.log("game", "action_done", tag=tag, text=text, kind="question", t_llm=round(t_llm, 1))
                    return
                start_frame = self.display.current_frame
                self.display.event({"type": "status", "text": f"Rendering (~{int(settings.clip_seconds * 11)} s): {branch.visible_result[:70]}", "tag": tag, "phase": "rendering"})
                t1 = time.time()
                with self.clip_lock:
                    frames = self.clip.render(start_frame, branch.clip_prompt, settings.clip_seconds, seed=n)
                t_clip = time.time() - t1
                self.display.event({"type": "status", "text": f"▶ Now playing: {text[:70]}", "tag": tag, "phase": "playing"})
                self.audit.submit(start_frame, frames, branch.expected_visible, tag)
                self.display.enqueue_clip(frames, tag=tag, source="plot" if plot else "clip")
                self.session.log("game", "action_done", tag=tag, text=text, success=success, roll=roll,
                                 t_llm=round(t_llm, 1), t_clip=round(t_clip, 1), notes=notes)
            except Exception as e:
                log.exception("action failed")
                self.session.log("game", "action_error", tag=tag, error=str(e)[:300])
                self.display.event({"type": "status", "text": f"(action failed: {str(e)[:120]})", "tag": tag})
                self.display.lock_keys(False)

    def _caption_view(self, frame: np.ndarray, version: int) -> str:
        """Perception: short VLM caption of the current frame (cached per display version)."""
        if self.view_cache[0] == version:
            return self.view_cache[1]
        if not self.vlm.available:
            return ""
        with self.view_lock:                      # one caption per version; others wait for it
            ev = self.view_inflight.get(version)
            if ev is None:
                ev = threading.Event()
                self.view_inflight[version] = ev
                owner = True
            else:
                owner = False
        if not owner:
            ev.wait(timeout=8)
            return self.view_cache[1] if self.view_cache[0] == version else ""
        p = self.session.frames / f"view_v{version}.jpg"
        Image.fromarray(frame).save(p, quality=85)
        try:
            cap = self.vlm.json("Describe the first-person view in one sentence for a film director.", "What is on screen?", [p], ViewCaption).view
        except Exception as e:
            self.session.log("vlm", "view_caption_error", error=str(e)[:200])
            cap = ""
        if cap:
            self.view_cache = (version, cap)
            self.session.log("vlm", "view_caption", version=version, view=cap)
        with self.view_lock:
            self.view_inflight.pop(version, None)
        ev.set()
        return cap

    def _regen_idle(self, frame: np.ndarray, version: int) -> None:
        """Background: render a fresh ambient loop from the new current frame (and caption it)."""
        threading.Thread(target=self._caption_view, args=(frame, version), daemon=True).start()
        st = self.session.state
        prompt = GMAgent.idle_prompt(st.scene.description, st.scene.style)
        if self.action_lock.locked():             # an action clip is coming; it will trigger its own idle regen
            return
        with self.clip_lock:
            if version != self.display.version:   # stale before we even started
                return
            t0 = time.time()
            frames = self.clip.render(frame, prompt, settings.idle_seconds, seed=version, steps=settings.idle_steps)
        self.session.log("game", "idle_rendered", version=version, seconds=round(time.time() - t0, 1))
        self.display.set_idle(frames, version)

    def _tick(self) -> None:
        """Called ~1/s from the display loop: fire due plot commitments."""
        if not self.started or self.action_lock.locked():
            return
        # nobody watching, or nobody has touched keys/text for a while -> the world waits
        if not self.display.subs or time.time() - self.display.last_input_t > settings.plot_idle_pause_s:
            return
        due = self.memory.due_commitments()
        now = self.session.state.elapsed()
        fresh = [c for c in due if now - c.trigger_seconds < 120]
        if len(fresh) < len(due):
            self.session.log("game", "plot_skipped_stale", events=[c.event for c in due if c not in fresh])
        if fresh:   # at most one plot beat at a time; later ones are rescheduled a minute apart
            threading.Thread(target=self._do_action, args=(fresh[0].event, True), daemon=True, name="plot").start()
            with self.session.lock:
                for k, c in enumerate(fresh[1:], 1):
                    c.fired = False
                    c.trigger_seconds = now + 60 * k
                self.session.save()

    def _push_state(self) -> None:
        st = self.session.state
        self.display.event({"type": "state", "state": st.model_dump(mode="json")})
