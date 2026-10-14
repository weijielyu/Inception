"""GPU-free stand-ins so the whole loop (display, web, GM) can be built and tested anywhere."""
from __future__ import annotations

import time

import numpy as np
from PIL import Image, ImageDraw

from .base import Keys


class MockARWalk:
    """Virtual camera over a 2x upscaled seed: W/S zoom, A/D pan, mouse pans. ~chunk of 4 frames."""
    name = "mock-ar"

    def __init__(self, width: int, height: int, fps: int = 16, chunk: int = 4):
        self.w, self.h, self.fps, self.chunk = width, height, fps, chunk
        self.canvas: Image.Image | None = None
        self.cx = self.cy = 0.5
        self.zoom = 1.0

    def start(self, frame: np.ndarray) -> None:
        self.canvas = Image.fromarray(frame).resize((self.w * 2, self.h * 2), Image.LANCZOS)
        self.cx = self.cy = 0.5
        self.zoom = 1.0

    def _view(self) -> np.ndarray:
        assert self.canvas is not None
        cw, ch = int(self.w / self.zoom), int(self.h / self.zoom)
        left = int(self.cx * self.canvas.width - cw / 2)
        top = int(self.cy * self.canvas.height - ch / 2)
        left = max(0, min(self.canvas.width - cw, left))
        top = max(0, min(self.canvas.height - ch, top))
        return np.asarray(self.canvas.crop((left, top, left + cw, top + ch)).resize((self.w, self.h)))

    def step(self, keys: Keys) -> list[np.ndarray]:
        frames = []
        for _ in range(self.chunk):
            if keys.w:
                self.zoom = min(2.0, self.zoom * 1.01)
            if keys.s:
                self.zoom = max(1.0, self.zoom / 1.01)
            if keys.a:
                self.cx = max(0.0, self.cx - 0.004)
            if keys.d:
                self.cx = min(1.0, self.cx + 0.004)
            self.cx = min(1.0, max(0.0, self.cx + keys.dx / 4000))
            self.cy = min(1.0, max(0.0, self.cy + keys.dy / 4000))
            frames.append(self._view())
        time.sleep(self.chunk / self.fps * 0.8)   # emulate ~real-time generation
        return frames


class MockClip:
    """Ken Burns on the start frame with the prompt burned in; sleeps to emulate generation latency."""
    name = "mock-clip"

    def __init__(self, width: int, height: int, fps: int = 16, latency_s: float = 3.0):
        self.w, self.h, self.fps, self.latency_s = width, height, fps, latency_s

    def render(self, frame: np.ndarray, prompt: str, seconds: float, seed: int = 0, steps: int | None = None) -> list[np.ndarray]:
        time.sleep(self.latency_s)
        img = Image.fromarray(frame).resize((self.w, self.h))
        n = int(seconds * self.fps)
        out = []
        for i in range(n):
            z = 1.0 + 0.12 * i / max(1, n - 1)
            cw, ch = int(self.w / z), int(self.h / z)
            left, top = (self.w - cw) // 2, (self.h - ch) // 2
            f = img.crop((left, top, left + cw, top + ch)).resize((self.w, self.h))
            d = ImageDraw.Draw(f)
            d.rectangle((0, self.h - 28, self.w, self.h), fill=(0, 0, 0))
            d.text((6, self.h - 22), prompt[:90], fill=(255, 255, 255))
            out.append(np.asarray(f))
        return out
