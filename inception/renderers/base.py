"""Renderer interfaces. Frames are HxWx3 uint8 numpy arrays."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class Keys:
    w: bool = False
    a: bool = False
    s: bool = False
    d: bool = False
    dx: float = 0.0   # mouse look, pixels per chunk
    dy: float = 0.0

    @property
    def any(self) -> bool:
        return self.w or self.a or self.s or self.d or abs(self.dx) > 1 or abs(self.dy) > 1


class ARWalkRenderer(Protocol):
    """Autoregressive world model: start from a frame, then produce chunks driven by keys."""
    name: str
    fps: int

    def start(self, frame: np.ndarray) -> None: ...
    def step(self, keys: Keys) -> list[np.ndarray]: ...


class ClipRenderer(Protocol):
    """Offline image-to-video clip generator (actions, idle loops)."""
    name: str
    fps: int

    def render(self, frame: np.ndarray, prompt: str, seconds: float, seed: int = 0, steps: int | None = None) -> list[np.ndarray]: ...
