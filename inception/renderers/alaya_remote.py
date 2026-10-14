"""AlayaWorld as the walk renderer, via the resident server in inception/alaya_server.py.

One step = one 32-frame chunk at 24 fps (1.33 s of walking) and takes ~6-10 s to generate on two
RTX 6000 Ada cards at 640x352, so walking arrives in bursts rather than in real time.
"""
from __future__ import annotations

import base64
import io
import logging

import httpx
import numpy as np
from PIL import Image

from ..config import settings
from .base import Keys

log = logging.getLogger("inception.alaya")


class AlayaRemoteWalk:
    name = "alayaworld"
    native_fps = 24

    def __init__(self, width: int, height: int, fps: int, url: str | None = None):
        self.w, self.h, self.fps = width, height, fps
        self.url = (url or settings.alaya_url).rstrip("/")
        self.prompt = "A first-person view of the scene, walking forward at a natural pace, no people in view."
        self.event_prompt: str | None = None      # optional one-off text event for the next steps
        self.client = httpx.Client(timeout=600)
        h = self.client.get(self.url + "/health").json()
        log.info("AlayaWorld server %s: %s", self.url, h)

    def start(self, frame: np.ndarray) -> None:
        buf = io.BytesIO(); Image.fromarray(frame).save(buf, format="PNG")
        r = self.client.post(self.url + "/start", json={"image_b64": base64.b64encode(buf.getvalue()).decode(), "prompt": self.prompt})
        r.raise_for_status()

    def step(self, keys: Keys) -> list[np.ndarray]:
        # W/S walk; A/D and mouse-x turn (strafing is nearly invisible at this model's motion scale)
        yaw = (1.0 if keys.d else 0.0) - (1.0 if keys.a else 0.0)
        if abs(keys.dx) > 1:
            yaw = 1.0 if keys.dx > 0 else -1.0
        pitch = (-1.0 if keys.dy > 1 else 1.0 if keys.dy < -1 else 0.0)
        body = {"forward": (1.0 if keys.w else 0.0) - (1.0 if keys.s else 0.0), "yaw": yaw, "pitch": pitch,
                "prompt": self.event_prompt or self.prompt}
        r = self.client.post(self.url + "/step", json=body)
        r.raise_for_status()
        frames = [np.asarray(Image.open(io.BytesIO(base64.b64decode(f))).convert("RGB").resize((self.w, self.h)))
                  for f in r.json()["frames"]]
        n_out = max(1, round(len(frames) * self.fps / self.native_fps))      # keep real-time speed at the display fps
        idx = np.linspace(0, len(frames) - 1, n_out).round().astype(int)
        return [frames[i] for i in idx]
