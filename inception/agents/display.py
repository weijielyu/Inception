"""Display agent: owns the play buffer and decides, every tick, which frame the player sees.

Three sources, one rule set:
  clip  — queued action/plot clips: always win; keys are locked while one plays
  ar    — the autoregressive walk model: frames generated while keys are held (and not locked);
          one long-lived worker owns the model, so its state always continues from the last frame shown
          and is only restarted after a clip or when banked forward frames have to be thrown away
  idle  — the last frame held still, replaced by a short ambient Wan clip (ping-ponged) once rendered
Every switch happens at the *current frame*; the last frame of whatever played becomes the new
current frame, and an idle-regeneration request is raised so the world keeps breathing.
"""
from __future__ import annotations

import io
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from PIL import Image

from ..config import settings
from ..renderers.base import ARWalkRenderer, Keys
from ..state import Session
from .qc import FrameQC


@dataclass
class PlayItem:
    source: str                      # clip | plot
    frames: list[np.ndarray]
    tag: str
    lock_keys: bool = True


@dataclass
class Subscriber:
    on_frame: Callable[[bytes], None]
    on_event: Callable[[dict], None]
    _dead: bool = field(default=False)


class DisplayAgent:
    name = "display"

    def __init__(self, session: Session, ar: ARWalkRenderer, fps: int, key_release_s: float = 1.5,
                 on_idle_needed: Callable[[np.ndarray, int], None] | None = None,
                 on_tick: Callable[[], None] | None = None):
        self.session, self.ar, self.fps = session, ar, fps
        self.on_idle_needed = on_idle_needed
        self.on_tick = on_tick
        self.qc = FrameQC()

        self.current_frame: np.ndarray | None = None
        self.last_shown: np.ndarray | None = None
        self.version = 0                      # bumps whenever current_frame changes
        self.idle: list[np.ndarray] = []
        self.idle_i, self.idle_dir = 0, 1
        self.clips: deque[PlayItem] = deque()
        self.playing: PlayItem | None = None
        self.play_i = 0
        self.keys = Keys()
        self.keys_locked = False
        self.last_input_t = time.time()       # last key press or typed action (plot clock pauses without them)
        self.mode = "idle"
        self.lock = threading.RLock()
        self.subs: list[Subscriber] = []
        self._stop = False
        self._thread: threading.Thread | None = None
        # walk model state (all guarded by self.lock; only the AR worker calls into self.ar)
        self.ar_buffer: deque[np.ndarray] = deque()   # generated frames waiting to be shown
        self.ar_synced = -1                   # display version the model state corresponds to (-1: needs start())
        self.ar_inflight = False              # a start()/step() call is running
        self.bank: list[np.ndarray] = []      # forward frames generated ahead while the player stands still
        self.bank_steps = 0
        self._waiting_since, self._told_waiting = 0.0, False
        self._rec = None
        if settings.record_stream:
            import imageio.v2 as iio2
            self._rec = iio2.get_writer(str(session.clips / "stream.mp4"), fps=fps, codec="libx264", quality=7, macro_block_size=1,
                                        output_params=["-movflags", "frag_keyframe+empty_moov"])  # readable while recording

    # ------------------------------------------------------------- lifecycle
    def start(self, frame: np.ndarray) -> None:
        with self.lock:
            self.current_frame = frame
            self.last_shown = frame
            self.idle = [frame]
            self.version += 1
        self._stop = False
        self._thread = threading.Thread(target=self._loop, daemon=True, name="display-loop")
        self._thread.start()
        threading.Thread(target=self._ar_loop, daemon=True, name="ar-worker").start()
        if self.on_idle_needed:
            self.on_idle_needed(frame, self.version)

    def stop(self) -> None:
        self._stop = True
        if self._rec is not None:
            try:
                self._rec.close()
            except Exception:
                pass
            self._rec = None

    # --------------------------------------------------------------- inputs
    def set_keys(self, keys: Keys) -> None:
        with self.lock:
            self.keys = keys
            if keys.any:
                self.last_input_t = time.time()

    def lock_keys(self, locked: bool) -> None:
        with self.lock:
            self.keys_locked = locked
        self.event({"type": "mode", "mode": self.mode, "keys_locked": locked})

    def enqueue_clip(self, frames: list[np.ndarray], tag: str, source: str = "clip") -> None:
        with self.lock:
            self.clips.append(PlayItem(source=source, frames=frames, tag=tag))

    def set_idle(self, frames: list[np.ndarray], version: int) -> None:
        with self.lock:
            if version != self.version or not frames:
                self.session.log(self.name, "idle_dropped_stale", version=version, current=self.version)
                return
            self.idle, self.idle_i, self.idle_dir = frames, 0, 1
        self.session.log(self.name, "idle_set", frames=len(frames), version=version)

    def subscribe(self, sub: Subscriber) -> None:
        self.subs.append(sub)

    def event(self, payload: dict) -> None:
        for s in list(self.subs):
            try:
                s.on_event(payload)
            except Exception:
                s._dead = True
        self.subs = [s for s in self.subs if not s._dead]

    # ------------------------------------------------------------ main loop
    def _loop(self) -> None:
        period = 1.0 / self.fps
        last_tick = 0.0
        while not self._stop:
            t0 = time.time()
            frame = self._next_frame()
            if frame is not None:
                self._publish(frame)
            if self.on_tick and t0 - last_tick > 1.0:
                last_tick = t0
                try:
                    self.on_tick()
                except Exception as e:
                    self.session.log(self.name, "tick_error", error=str(e)[:200])
            dt = time.time() - t0
            if dt < period:
                time.sleep(period - dt)

    def _next_frame(self) -> np.ndarray | None:
        with self.lock:
            # 1. a clip is playing
            if self.playing is not None:
                if self.play_i < len(self.playing.frames):
                    f = self.playing.frames[self.play_i]
                    self.play_i += 1
                    return f
                self._finish_clip()
            # 2. a clip is queued
            if self.clips:
                self.playing, self.play_i = self.clips.popleft(), 0
                self.keys_locked = True
                self.ar_buffer.clear(); self.bank, self.bank_steps = [], 0
                self.ar_synced = -1               # the clip moves the world; the walk model restarts after it
                self._set_mode("clip")
                f = self.playing.frames[0]
                self.play_i = 1
                return f
            # 3. walking
            held = self.keys.any and not self.keys_locked
            if held and self.mode != "ar":
                self._set_mode("ar")
                self._waiting_since = time.time()
            if self.mode == "ar":
                if self.ar_buffer:
                    self._waiting_since, self._told_waiting = 0.0, False
                    return self.ar_buffer.popleft()
                if held or self.ar_inflight:
                    if held and not self._waiting_since:
                        self._waiting_since = time.time()
                    if self._waiting_since and time.time() - self._waiting_since > 0.7 and not self._told_waiting:
                        self._told_waiting = True
                        self.event({"type": "status", "text": "Generating the next steps…", "phase": "rendering"})
                    return self.last_shown            # nothing generated yet: hold the frame
                self._adopt_walk()
            # 4. idle
            if not self.idle:
                return self.current_frame
            f = self.idle[self.idle_i]
            if len(self.idle) > 1:
                self.idle_i += self.idle_dir
                if self.idle_i >= len(self.idle) or self.idle_i < 0:
                    self.idle_dir *= -1
                    self.idle_i += 2 * self.idle_dir
            return f

    def _adopt_walk(self) -> None:
        """Walking ended and every generated frame was shown: the last one becomes the current frame."""
        moved = self.last_shown is not self.current_frame
        if moved:
            self.current_frame = self.last_shown
            self.version += 1
            # the model is exactly at this frame unless forward frames were banked ahead of it
            self.ar_synced = self.version if self.bank_steps == 0 else -1
            self.bank, self.bank_steps = [], 0
            self.idle = [self.current_frame]
            self.idle_i, self.idle_dir = 0, 1
            if self.on_idle_needed:
                threading.Thread(target=self.on_idle_needed, args=(self.current_frame, self.version), daemon=True).start()
        self._set_mode("idle")

    def _finish_clip(self) -> None:
        item = self.playing
        self.playing = None
        if item and item.frames:
            self.current_frame = item.frames[-1]
            self.version += 1
            self.idle = [self.current_frame]          # hold the last frame until the Wan idle loop arrives
            self.idle_i, self.idle_dir = 0, 1
            if self.on_idle_needed:
                threading.Thread(target=self.on_idle_needed, args=(self.current_frame, self.version), daemon=True).start()
        if not self.clips:
            self.keys_locked = False
        self._set_mode("idle")
        self.session.log(self.name, "clip_done", tag=item.tag if item else None)

    def _set_mode(self, mode: str) -> None:
        if mode != self.mode:
            self.mode = mode
            self.event({"type": "mode", "mode": mode, "keys_locked": self.keys_locked})

    # ------------------------------------------------------------------- AR
    def _ar_loop(self) -> None:
        """The only thread that talks to the walk model."""
        while not self._stop:
            try:
                with self.lock:
                    v, k = self.version, self.keys
                    busy = self.keys_locked or self.playing is not None or bool(self.clips)
                    held = k.any and not busy
                    synced = self.ar_synced == v
                    forward_only = k.w and not (k.a or k.s or k.d or abs(k.dx) > 1 or abs(k.dy) > 1)
                    room = len(self.ar_buffer) < self.fps * settings.ar_buffer_seconds
                    frame = self.last_shown if self.mode == "ar" else self.current_frame
                if busy or frame is None:
                    time.sleep(0.05); continue
                if not synced:                                   # (re)start the model from what is on screen
                    self._call(lambda: self.ar.start(frame))
                    with self.lock:
                        if self.version == v:
                            self.ar_synced, self.bank, self.bank_steps = v, [], 0
                    self.qc.reset()
                    self.session.log(self.name, "ar_synced", version=v)
                    continue
                if held:
                    with self.lock:
                        if self.bank_steps:
                            if forward_only:                     # play what was generated ahead
                                self.ar_buffer.extend(self.bank)
                                self.session.log(self.name, "ar_bank_used", frames=len(self.bank))
                                self.bank, self.bank_steps = [], 0
                            else:                                # model is ahead in a direction the player did not take
                                self.bank, self.bank_steps, self.ar_synced = [], 0, -1
                                continue
                    if not room:
                        time.sleep(0.02); continue
                    frames = self._call(lambda: self.ar.step(k))
                    good = [f for f in frames if self.qc.check(f)[0]]
                    ok, reason = self.qc.drift(good)
                    with self.lock:
                        if self.version != v or self.ar_synced != v:
                            continue                             # a clip intervened; drop these frames
                        if not ok or len(good) < len(frames) // 2:
                            self.session.log(self.name, "ar_reseed", reason=reason, dropped=len(frames) - len(good))
                            self.ar_synced = -1
                            continue
                        self.ar_buffer.extend(good)
                elif self.mode == "idle" and self.bank_steps < settings.ar_prefetch_chunks:
                    frames = self._call(lambda: self.ar.step(Keys(w=True)))   # speculative forward walk
                    with self.lock:
                        if self.version == v and self.ar_synced == v:
                            self.bank.extend(frames); self.bank_steps += 1
                    self.session.log(self.name, "ar_banked", version=v, steps=self.bank_steps)
                else:
                    time.sleep(0.05)
            except Exception as e:
                self.session.log(self.name, "ar_error", error=str(e)[:300])
                with self.lock:
                    self.ar_synced = -1
                time.sleep(2)

    def _call(self, fn):
        self.ar_inflight = True
        try:
            return fn()
        finally:
            self.ar_inflight = False

    # ------------------------------------------------------------- publish
    def _publish(self, frame: np.ndarray) -> None:
        self.last_shown = frame
        if self._rec is not None:
            try:
                self._rec.append_data(frame)
            except Exception as e:
                self.session.log(self.name, "record_error", error=str(e)[:120])
                self._rec = None
        if not self.subs:
            return
        buf = io.BytesIO()
        Image.fromarray(frame).save(buf, format="JPEG", quality=80)
        data = buf.getvalue()
        for s in list(self.subs):
            try:
                s.on_frame(data)
            except Exception:
                s._dead = True
        self.subs = [s for s in self.subs if not s._dead]
