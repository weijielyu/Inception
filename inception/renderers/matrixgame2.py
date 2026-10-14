"""Matrix-Game 2.0 as a resident, step-wise autoregressive walk renderer.

Re-implements the per-block loop of `CausalInferenceStreamingPipeline.inference` so that
keyboard/mouse conditions can be supplied live for each block (3 latent frames -> 12 pixel
frames, 9 for the very first block) instead of via `input()`.

Expects the upstream code at third_party/Matrix-Game/Matrix-Game-2 and the weights at
settings.matrixgame2_dir (Skywork/Matrix-Game-2.0 snapshot).
"""
from __future__ import annotations

import copy
import logging
import sys
import threading
import time
from pathlib import Path

import numpy as np
import torch

from ..config import ROOT, settings
from . import _flash_attn_shim
from .base import Keys
from .gpu import pick_gpu

log = logging.getLogger("inception.mg2")
MG2_SRC = ROOT / "third_party/Matrix-Game/Matrix-Game-2"
CAM_VALUE = 0.1


class MatrixGame2Walk:
    name = "matrix-game-2.0"

    def __init__(self, width: int = 640, height: int = 352, fps: int = 16, model_dir: str | None = None,
                 device: str | None = None, max_latents: int = 360, mode: str = "universal", warmup: bool = True):
        assert (width, height) == (640, 352), "Matrix-Game 2.0 is trained at 640x352"
        self.w, self.h, self.fps = width, height, fps
        self.mode = mode
        self.max_latents = max_latents            # noise is pre-allocated for this horizon, then we re-seed
        self.device = torch.device(device or pick_gpu())
        self.dtype = torch.bfloat16
        self.lock = threading.Lock()
        self.model_dir = Path(model_dir or settings.matrixgame2_dir)
        if _flash_attn_shim.install():
            log.warning("flash_attn not installed: using SDPA shim (slower)")
        if str(MG2_SRC) not in sys.path:
            sys.path.insert(0, str(MG2_SRC))
        self._load()
        self._reset_session()
        if warmup:
            self._warmup()

    def _warmup(self) -> None:
        """Trigger torch.compile / cudnn autotuning at boot instead of on the player's first step."""
        t0 = time.time()
        dummy = (np.random.default_rng(0).random((self.h, self.w, 3)) * 255).astype(np.uint8)
        self.start(dummy)
        for _ in range(8):
            self.step(Keys(w=True))
        self._reset_session()
        log.info("Matrix-Game 2.0 warm-up done in %.0fs", time.time() - t0)

    # ------------------------------------------------------------------ load
    def _load(self) -> None:
        from omegaconf import OmegaConf
        from safetensors.torch import load_file
        from torchvision.transforms import v2

        from demo_utils.vae_block3 import VAEDecoderWrapper
        from pipeline import CausalInferenceStreamingPipeline
        from utils.wan_wrapper import WanDiffusionWrapper
        from wan.vae.wanx_vae import get_wanx_vae_wrapper

        t0 = time.time()
        cfg = OmegaConf.load(MG2_SRC / f"configs/inference_yaml/inference_{self.mode}.yaml")
        cfg.model_kwargs.model_config = str(MG2_SRC / cfg.model_kwargs.model_config)
        cfg.pop("mode", None)
        self.cfg = cfg
        with torch.cuda.device(self.device):
            generator = WanDiffusionWrapper(**cfg.model_kwargs, is_causal=True)
            dec = VAEDecoderWrapper()
            sd = torch.load(self.model_dir / "Wan2.1_VAE.pth", map_location="cpu")
            dec.load_state_dict({k: v for k, v in sd.items() if "decoder." in k or "conv2" in k})
            dec.to(self.device, torch.float16).requires_grad_(False).eval()
            pipe = CausalInferenceStreamingPipeline(cfg, generator=generator, vae_decoder=dec)
            ckpt = self.model_dir / ("base_distilled_model/base_distill.safetensors" if self.mode == "universal"
                                     else "templerun_distilled_model/templerun_7dim_onlykey.safetensors")
            pipe.generator.load_state_dict(load_file(ckpt))
            self.pipe = pipe.to(device=self.device, dtype=self.dtype)
            self.pipe.vae_decoder.to(torch.float16)
            vae = get_wanx_vae_wrapper(str(self.model_dir), torch.float16)
            vae.requires_grad_(False).eval()
            self.vae = vae.to(self.device, self.dtype)
        self.frame_process = v2.Compose([
            v2.Resize(size=(352, 640), antialias=True),
            v2.ToTensor(),
            v2.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])
        log.info("Matrix-Game 2.0 loaded on %s in %.0fs", self.device, time.time() - t0)

    def _reset_session(self) -> None:
        self.cond = None
        self.noise = None
        self.cur = 0
        self.vae_cache = None
        self.last_frame: np.ndarray | None = None

    # ----------------------------------------------------------------- start
    @torch.no_grad()
    def start(self, frame: np.ndarray) -> None:
        from PIL import Image

        with self.lock, torch.cuda.device(self.device):
            self._reset_session()
            img = Image.fromarray(frame).convert("RGB")
            x = self.frame_process(img)[None, :, None].to(self.device, self.dtype)       # [1,3,1,H,W]
            # Upstream encodes [image + zeros] for the whole horizon (23 s for 360 latents). The zero-padded
            # tail reaches a steady state after the causal VAE's receptive field, so encode a short prefix
            # and replicate its last latent: measured identical (max |diff| 0.0000) at 33 latents, ~2 s.
            n_enc = min(self.max_latents, 33)
            pad = torch.zeros_like(x).repeat(1, 1, 4 * (n_enc - 1), 1, 1)
            enc = self.vae.encode(torch.cat([x, pad], dim=2), device=self.device, tiled=False).to(self.device)
            img_cond = torch.cat([enc, enc[:, :, -1:].repeat(1, 1, self.max_latents - n_enc, 1, 1)], dim=2)
            mask = torch.ones_like(img_cond)
            mask[:, :, 1:] = 0
            n_px = 1 + 4 * (self.max_latents - 1)
            self.cond = {
                "cond_concat": torch.cat([mask[:, :4], img_cond], dim=1).to(self.device, self.dtype),
                "visual_context": self.vae.clip.encode_video(x).to(self.device, self.dtype),
                "keyboard_cond": torch.zeros([1, n_px, 4], device=self.device, dtype=self.dtype),
                "mouse_cond": torch.zeros([1, n_px, 2], device=self.device, dtype=self.dtype),
            }
            self.noise = torch.randn([1, 16, self.max_latents, 44, 80], device=self.device, dtype=self.dtype)
            self._init_caches()
            from demo_utils.constant import ZERO_VAE_CACHE
            self.vae_cache = [None for _ in copy.deepcopy(ZERO_VAE_CACHE)]
            self.cur = 0
            self.last_frame = np.asarray(img.resize((self.w, self.h)))

    def _init_caches(self) -> None:
        p = self.pipe
        p.kv_cache1 = p.kv_cache_mouse = p.kv_cache_keyboard = p.crossattn_cache = None
        p._initialize_kv_cache(batch_size=1, dtype=self.dtype, device=self.device)
        p._initialize_kv_cache_mouse_and_keyboard(batch_size=1, dtype=self.dtype, device=self.device)
        p._initialize_crossattn_cache(batch_size=1, dtype=self.dtype, device=self.device)

    # ------------------------------------------------------------------ step
    @staticmethod
    def _actions(keys: Keys) -> dict[str, torch.Tensor]:
        kb = [1.0 if keys.w else 0.0, 1.0 if keys.s else 0.0, 1.0 if keys.a else 0.0, 1.0 if keys.d else 0.0]
        # mouse: [pitch, yaw] in the model's unit; browser dx>0 = look right
        yaw = CAM_VALUE if keys.dx > 1 else (-CAM_VALUE if keys.dx < -1 else 0.0)
        pitch = -CAM_VALUE if keys.dy > 1 else (CAM_VALUE if keys.dy < -1 else 0.0)
        return {"keyboard": torch.tensor(kb), "mouse": torch.tensor([pitch, yaw])}

    @torch.no_grad()
    def step(self, keys: Keys) -> list[np.ndarray]:
        from einops import rearrange

        from pipeline.causal_inference import cond_current

        with self.lock, torch.cuda.device(self.device):
            if self.cond is None:
                raise RuntimeError("call start() first")
            p = self.pipe
            nfb = p.num_frame_per_block
            if self.cur + nfb > self.max_latents:          # horizon exhausted: re-seed from last frame
                log.info("horizon reached, re-seeding from last frame")
                self.start(self.last_frame)
            acts = {k: v.to(self.device, self.dtype) for k, v in self._actions(keys).items()}
            new_act, self.cond = cond_current(self.cond, self.cur, nfb, replace=acts, mode=self.mode)
            noisy = self.noise[:, :, self.cur:self.cur + nfb]
            start_tok = self.cur * p.frame_seq_length
            steps = p.denoising_step_list
            for i, t in enumerate(steps):
                timestep = torch.ones([1, nfb], device=self.device, dtype=torch.int64) * t
                _, pred = p.generator(noisy_image_or_video=noisy, conditional_dict=new_act, timestep=timestep,
                                      kv_cache=p.kv_cache1, kv_cache_mouse=p.kv_cache_mouse,
                                      kv_cache_keyboard=p.kv_cache_keyboard, crossattn_cache=p.crossattn_cache,
                                      current_start=start_tok)
                if i < len(steps) - 1:
                    nxt = steps[i + 1]
                    flat = rearrange(pred, "b c f h w -> (b f) c h w")
                    noisy = p.scheduler.add_noise(flat, torch.randn_like(flat),
                                                  nxt * torch.ones([nfb], device=self.device, dtype=torch.long))
                    noisy = rearrange(noisy, "(b f) c h w -> b c f h w", b=1)
            # update KV cache with the clean block
            ctx_t = torch.ones([1, nfb], device=self.device, dtype=torch.int64) * self.cfg.context_noise
            p.generator(noisy_image_or_video=pred, conditional_dict=new_act, timestep=ctx_t,
                        kv_cache=p.kv_cache1, kv_cache_mouse=p.kv_cache_mouse, kv_cache_keyboard=p.kv_cache_keyboard,
                        crossattn_cache=p.crossattn_cache, current_start=start_tok)
            video, self.vae_cache = p.vae_decoder(pred.transpose(1, 2).half(), *self.vae_cache)
            self.cur += nfb
            video = rearrange(video, "B T C H W -> B T H W C")
            frames = ((video.float() + 1) * 127.5).clip(0, 255).to(torch.uint8).cpu().numpy()[0]
            frames = [np.ascontiguousarray(f) for f in frames]
            self.last_frame = frames[-1]
            return frames
