"""Display agent: owns the play buffer and decides, every tick, which frame the player sees.

Three sources, one rule set:
  clip  — queued action/plot clips: always win; keys are locked while one plays
  ar    — the autoregressive walk model: used while keys are held (and not locked)
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
        self.key_release_s = key_release_s
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
        self.last_key_t = 0.0
        self.last_input_t = time.time()       # last key press or typed action (plot clock pauses without them)
        self.mode = "idle"
        self.ar_buffer: deque[np.ndarray] = deque()
        self.ar_thread: threading.Thread | None = None
        self.ar_active = False
        self.lock = threading.RLock()
        self.subs: list[Subscriber] = []
        self._stop = False
        self._thread: threading.Thread | None = None
        self.ar_frames_recent: deque[np.ndarray] = deque(maxlen=fps * 2)
        self.prepared_version = -1            # AR renderer has been start()ed on this version's frame
        self._prepare_done: dict[int, threading.Event] = {}
        self.ar_lock = threading.Lock()       # serializes every call into the AR renderer
        self.prefetch: list[np.ndarray] = []  # forward frames generated ahead of the player (slow renderers)
        self.prefetch_version = -1
        self.prefetch_steps = 0
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
        if self.on_idle_needed:
            self.on_idle_needed(frame, self.version)
        self._prepare_ar()

    def _prepare_ar(self) -> None:
        """Encode the current frame into the AR model in the background so the first step is instant."""
        version, frame = self.version, self.current_frame
        done = threading.Event()
        self._prepare_done[version] = done

        def run():
            try:
                with self.ar_lock:
                    self.ar.start(frame)
                with self.lock:
                    if self.version == version:
                        self.prepared_version = version
                        self.prefetch, self.prefetch_version, self.prefetch_steps = [], version, 0
                self.session.log(self.name, "ar_prepared", version=version)
            except Exception as e:
                self.session.log(self.name, "ar_prepare_error", error=str(e)[:200])
            finally:
                done.set()
                self._prepare_done.pop(version, None)
            # Speculative walk: bank a few forward chunks while the player stands still, so pressing W
            # plays immediately even when the renderer is slower than real time.
            try:
                for _ in range(settings.ar_prefetch_chunks):
                    if self._stop or self.ar_active or self.version != version:
                        break
                    with self.ar_lock:
                        if self.ar_active or self.version != version:
                            break
                        frames = self.ar.step(Keys(w=True))
                        with self.lock:
                            if self.version == version:
                                self.prefetch.extend(frames)
                                self.prefetch_steps += 1
                if settings.ar_prefetch_chunks:
                    self.session.log(self.name, "ar_prefetched", version=version, frames=len(self.prefetch))
            except Exception as e:
                self.session.log(self.name, "ar_prefetch_error", error=str(e)[:200])

        threading.Thread(target=run, daemon=True, name="ar-prepare").start()

    def stop(self) -> None:
        self._stop = True
        self.ar_active = False
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
                self.last_key_t = self.last_input_t = time.time()

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
                self._stop_ar(adopt=False)
                self._set_mode("clip")
                return self._next_frame_unlocked()
            # 3. walking
            held = self.keys.any and not self.keys_locked
            if held:
                self.last_key_t = time.time()      # release timer counts from the last held tick
            if held and self.mode != "ar":
                self._start_ar()
            if self.mode == "ar":
                if not held and time.time() - self.last_key_t > self.key_release_s:
                    self._stop_ar(adopt=True)
                    self._set_mode("idle")
                else:
                    if self.ar_buffer:
                        f = self.ar_buffer.popleft()
                        self.ar_frames_recent.append(f)
                        return f
                    return self.last_shown
            # 4. idle ping-pong
            if not self.idle:
                return self.current_frame
            f = self.idle[self.idle_i]
            if len(self.idle) > 1:
                self.idle_i += self.idle_dir
                if self.idle_i >= len(self.idle) or self.idle_i < 0:
                    self.idle_dir *= -1
                    self.idle_i += 2 * self.idle_dir
            return f

    def _next_frame_unlocked(self):
        assert self.playing is not None
        f = self.playing.frames[0]
        self.play_i = 1
        return f

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
            self._prepare_ar()
        if not self.clips:
            self.keys_locked = False
        self._set_mode("idle")
        self.session.log(self.name, "clip_done", tag=item.tag if item else None)

    def _set_mode(self, mode: str) -> None:
        if mode != self.mode:
            self.mode = mode
            self.event({"type": "mode", "mode": mode, "keys_locked": self.keys_locked})

    # ------------------------------------------------------------------- AR
    def _start_ar(self) -> None:
        self.ar_buffer.clear()
        self.ar_frames_recent.clear()
        self.ar_active = True
        self._set_mode("ar")
        self.ar_thread = threading.Thread(target=self._ar_worker, args=(self.current_frame,), daemon=True, name="ar-worker")
        self.ar_thread.start()

    def _stop_ar(self, adopt: bool) -> None:
        self.ar_active = False
        if adopt and self.last_shown is not None and self.mode == "ar":
            self.current_frame = self.last_shown
            self.version += 1
            self.idle = [self.current_frame]          # hold the last frame (no ping-pong of walking frames)
            self.idle_i, self.idle_dir = 0, 1
            if self.on_idle_needed:
                threading.Thread(target=self.on_idle_needed, args=(self.current_frame, self.version), daemon=True).start()
            self._prepare_ar()
        self.ar_buffer.clear()

    def _ar_worker(self, seed_frame: np.ndarray) -> None:
        t0 = time.time()
        try:
            with self.lock:
                version = self.version
                pending = self._prepare_done.get(version)
            if pending is not None:                 # a pre-start for this frame is in flight: wait for it
                pending.wait(timeout=15)
            with self.ar_lock:                      # also waits for an in-flight prefetch step
                with self.lock:
                    prepared = self.prepared_version == version
                    k = self.keys
                    forward_only = k.w and not (k.a or k.s or k.d or abs(k.dx) > 1 or abs(k.dy) > 1)
                    banked = self.prefetch if self.prefetch_version == version else []
                    advanced = self.prefetch_steps if self.prefetch_version == version else 0
                    self.prefetch, self.prefetch_steps = [], 0
                if prepared and advanced and forward_only:
                    self.ar_buffer.extend(banked)       # play what was generated ahead; the model is already there
                elif not prepared or advanced:
                    self.ar.start(seed_frame)           # model is not at the displayed frame: restart from it
                    banked = []
            self.qc.reset()
            self.session.log(self.name, "ar_started", seconds=round(time.time() - t0, 2), prepared=prepared, banked=len(banked))
            while self.ar_active and not self._stop:
                if len(self.ar_buffer) > self.fps * settings.ar_buffer_seconds:   # don't run too far ahead of playback
                    time.sleep(0.02)
                    continue
                with self.ar_lock:
                    if not self.ar_active:
                        break
                    frames = self.ar.step(self.keys)
                good = [f for f in frames if self.qc.check(f)[0]]
                ok, reason = self.qc.drift(good)
                if not ok or len(good) < len(frames) // 2:
                    self.session.log(self.name, "ar_reseed", reason=reason, dropped=len(frames) - len(good))
                    with self.ar_lock:
                        self.ar.start(self.last_shown if self.last_shown is not None else seed_frame)
                    self.qc.reset()
                    continue
                self.ar_buffer.extend(good)
        except Exception as e:
            self.session.log(self.name, "ar_error", error=str(e)[:300])
            self.ar_active = False
            with self.lock:
                self._set_mode("idle")

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
