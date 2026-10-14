"""Wan2.2-TI2V-5B image-to-video clip renderer (DiffSynth), used for action and idle clips.

Loads once onto one GPU and renders short clips from the current displayed frame.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from ..config import settings
from .gpu import pick_gpu

log = logging.getLogger("inception.wan_clip")

NEG_DEFAULT = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，"
               "JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，"
               "手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走")


class WanClip:
    name = "wan2.2-ti2v-5b"

    def __init__(self, width: int, height: int, fps: int, model_dir: str | None = None, device: str | None = None,
                 steps: int | None = None, render_size: tuple[int, int] | None = None):
        self.w, self.h, self.fps = width, height, fps          # display size
        self.rw, self.rh = render_size or (width, height)      # generation size (e.g. 832x480 -> better clips, ~2x time)
        self.steps = steps or settings.video_steps
        self.device = device or pick_gpu()
        self.lock = threading.Lock()
        d = Path(model_dir or settings.wan_model_dir)
        t0 = time.time()
        from diffsynth.pipelines.wan_video import ModelConfig, WanVideoPipeline

        self.pipe = WanVideoPipeline.from_pretrained(
            torch_dtype=torch.bfloat16,
            device=self.device,
            model_configs=[
                ModelConfig(path=str(d / "models_t5_umt5-xxl-enc-bf16.pth")),
                ModelConfig(path=sorted(str(p) for p in d.glob("diffusion_pytorch_model*.safetensors"))),
                ModelConfig(path=str(d / "Wan2.2_VAE.pth")),
            ],
            tokenizer_config=ModelConfig(path=str(d / "google/umt5-xxl")),
        )
        log.info("Wan2.2 TI2V-5B loaded on %s in %.0fs", self.device, time.time() - t0)

    def render(self, frame: np.ndarray, prompt: str, seconds: float, seed: int = 0, steps: int | None = None) -> list[np.ndarray]:
        # Wan2.2 5B VAE: 4x temporal compression -> frames must be 4k+1
        n = int(round(seconds * self.fps))
        n = max(5, (n // 4) * 4 + 1)
        img = Image.fromarray(frame).convert("RGB").resize((self.rw, self.rh))
        with self.lock:
            t0 = time.time()
            video = self.pipe(
                prompt=prompt,
                negative_prompt=NEG_DEFAULT,
                input_image=img,
                seed=seed,
                tiled=True,
                height=self.rh,
                width=self.rw,
                num_frames=n,
                num_inference_steps=steps or self.steps,
            )
            dt = time.time() - t0
        log.info("clip %d frames @%dx%d in %.1fs (%.2f s/frame)", n, self.rw, self.rh, dt, dt / n)
        out = []
        for f in video:
            im = f if isinstance(f, Image.Image) else Image.fromarray(np.asarray(f))
            im = im.convert("RGB")
            if (self.rw, self.rh) != (self.w, self.h):
                im = im.resize((self.w, self.h), Image.LANCZOS)
            out.append(np.asarray(im))
        return out
