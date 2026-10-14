"""Resident AlayaWorld walk server: loads the model once, then serves start/step over HTTP.

Run with the AlayaWorld env on a host with two free GPUs (main model on the first, Gemma + DA3 on the second):

    cd third_party/AlayaWorld && ALAYA_TEXT_DEVICE=cuda:1 CUDA_VISIBLE_DEVICES=<a>,<b> \
        ../../.venv_alaya/bin/python ../../inception/alaya_server.py --cfg configs/infer_pt_352.yaml --port 8770

The per-chunk logic mirrors AlayaWorld's own interactive adapter (reactor/alayaworld.py: _reset_rollout,
_generate_chunk, _write_camera_trajectory, _decode_new_frames) without the reactor runtime dependency.
One chunk = 32 frames at 24 fps (1.33 s). Frames are returned as a JPEG list.
"""
from __future__ import annotations

import argparse
import base64
import io
import sys
import threading
import time
from pathlib import Path

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps
from pydantic import BaseModel

REPO = Path.cwd()                      # must be third_party/AlayaWorld
sys.path.insert(0, str(REPO))
from alaya.config.loader import load_config                      # noqa: E402
from alaya.inference.pipeline import FlashAlayaPipeline          # noqa: E402
from alaya.inference.rollout_utils import build_engine, check_input_resolution, plan_rollout  # noqa: E402
from inference.da3_patch import apply_da3_robust_scale          # noqa: E402
from reactor.alayaworld_camera import CameraMotionPlanner, MotionConfig  # noqa: E402

MOTION = dict(strafe_units_per_second=0.126, vertical_units_per_second=0.261, forward_units_per_second=1.905,
              pitch_degrees_per_second=4.039, yaw_degrees_per_second=9.375, roll_degrees_per_second=4.094)
MAX_SPATIAL, RECENT_SPATIAL, DECODE_OVERLAP, MAX_CHUNKS = 320, 160, 6, 512

app = FastAPI(title="AlayaWorld walk server")
LOCK = threading.Lock()
S: dict = {}   # engine, pipe, cfg, layout, cache, camera, ar_index, prompt


def cam_frames(c):
    return c if c.dim() == 3 else c[0]


def ensure_capacity(camera, n):
    cur = int(cam_frames(camera).shape[0])
    if cur >= n:
        return camera
    axis = 0 if camera.dim() == 3 else 1
    tail = camera[-1:] if camera.dim() == 3 else camera[:, -1:]
    rep = [1] * camera.dim(); rep[axis] = n - cur
    return torch.cat([camera, tail.repeat(*rep)], dim=axis)


def compact(cache):
    preds = getattr(cache, "preds", None)
    if isinstance(preds, list) and len(preds) > 1:
        preds[:] = preds[-1:]
    bank = getattr(cache, "spatial_bank", None)
    if bank is None:
        return
    total = len(bank.frame_indices)
    if total <= MAX_SPATIAL:
        return
    recent = min(RECENT_SPATIAL, MAX_SPATIAL)
    hist_n, budget = total - recent, MAX_SPATIAL - recent
    hist = [i * (hist_n - 1) // (budget - 1) for i in range(budget)] if budget > 1 else ([0] if budget == 1 else [])
    keep = hist + list(range(hist_n, total))
    bank.pixels = [bank.pixels[i] for i in keep]
    bank.frame_indices = [bank.frame_indices[i] for i in keep]
    bank.depths = [bank.depths[i] for i in keep]
    wp = getattr(bank, "world_points", None)
    if isinstance(wp, dict):
        bank.world_points = {n: wp[o] for n, o in enumerate(keep) if o in wp}


def load(cfg_path: str, compile_mode: str):
    cfg = load_config(cfg_path)
    engine = build_engine(cfg, compile_mode=compile_mode, compile_aux=False, bank_taehv=False, verbose=True)
    apply_da3_robust_scale()
    mode = next(iter(cfg.validation.modes.values()))
    K = int(mode.layout.output_latent_frames)
    N = int(cfg.layout.history_latent_frames if mode.layout.history_latent_frames is None else mode.layout.history_latent_frames)
    gap = int(float(mode.layout.max_gap_sec or 0.0) * cfg.sample.fps / cfg.sample.temporal_stride)
    cond_end = int(mode.layout.condition_latent_frames)
    pipe = FlashAlayaPipeline(engine, control_modes=list(mode.control), use_memory=bool(mode.use_memory),
                              action_cfg_scale=float(mode.action_cfg_scale), flex_attn=False, seed=1234, ttc=False,
                              ttc_levels=tuple(int(x) for x in cfg.validation.ttc.levels),
                              ttc_strength=float(cfg.validation.ttc.strength),
                              ttc_ref_action=bool(cfg.validation.ttc.ref_action))
    S.update(engine=engine, pipe=pipe, cfg=cfg, K=K, N=N, gap=gap, cond_end=cond_end,
             template=torch.load(REPO / "playground/case1/case1_camera.pt", map_location="cpu", weights_only=False))


class StartReq(BaseModel):
    image_b64: str
    prompt: str
    seed: int = 1234


class StepReq(BaseModel):
    forward: float = 0.0
    strafe: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    prompt: str | None = None
    quality: int = 85


@app.get("/health")
def health():
    return {"ok": "pipe" in S, "started": S.get("cache") is not None, "chunk": S.get("ar_index", 0),
            "size": [int(S["cfg"].sample.width), int(S["cfg"].sample.height)] if "cfg" in S else None, "fps": 24, "frames_per_chunk": 32}


@app.post("/start")
@torch.no_grad()
def start(req: StartReq):
    with LOCK:
        t0 = time.perf_counter()
        cfg, pipe = S["cfg"], S["pipe"]
        H, W = int(cfg.sample.height), int(cfg.sample.width)
        img = ImageOps.fit(ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(req.image_b64)))).convert("RGB"),
                           (W, H), method=Image.Resampling.LANCZOS)
        frame = torch.from_numpy(np.array(img, dtype=np.uint8, copy=True)).permute(2, 0, 1).float() / 127.5 - 1.0
        meta = {k: (v.clone() if hasattr(v, "clone") else v) for k, v in S["template"].items()}
        video = frame.unsqueeze(0).expand(int(cam_frames(meta["cam_c2w"]).shape[0]), -1, -1, -1).contiguous()
        check_input_resolution(video, cfg)
        video, meta, rounds, _max, needed = plan_rollout(cfg, video, meta, rounds_cap=1, K=S["K"], N=S["N"],
                                                         gap_steps=S["gap"], cond_end=S["cond_end"])
        S["cache"] = None
        pipe.seed = req.seed
        cache = pipe.initialize_cache(video, req.prompt, meta, rounds=1, K=S["K"], cond_end=S["cond_end"], needed_latents=needed)
        stride = int(cfg.sample.temporal_stride)
        anchor = max(0, int(cache.target_base_start) * stride - stride)
        pose0 = cam_frames(meta["cam_c2w"])[anchor].detach().cpu().to(torch.float32).numpy()
        S.update(cache=cache, ar_index=0, prompt=req.prompt,
                 camera=CameraMotionPlanner(pose0, MotionConfig(fps=float(cfg.sample.fps), **MOTION)))
        return {"ok": True, "seconds": round(time.perf_counter() - t0, 2)}


@app.post("/step")
@torch.no_grad()
def step(req: StepReq):
    with LOCK:
        cache, pipe, engine, cfg = S.get("cache"), S["pipe"], S["engine"], S["cfg"]
        if cache is None:
            return JSONResponse({"error": "call /start first"}, status_code=409)
        if S["ar_index"] >= MAX_CHUNKS:
            return JSONResponse({"error": "rollout exhausted; call /start"}, status_code=410)
        t0 = time.perf_counter()
        if req.prompt and req.prompt != S["prompt"]:
            cache.context = engine.encode_caption(req.prompt)
            S["prompt"] = req.prompt
        i, stride = S["ar_index"], int(cfg.sample.temporal_stride)
        px_start = int(cache.target_start(i)) * stride
        px_end = px_start + int(cache.K) * stride
        w_start = max(0, px_start - stride + 1) if i == 0 else px_start
        traj = S["camera"].plan(strafe=req.strafe, vertical=0.0, forward=req.forward, pitch=req.pitch, yaw=req.yaw,
                                roll=0.0, frame_count=px_end - w_start)
        cam = ensure_capacity(cache.metadata["cam_c2w"], px_end)
        vals = torch.from_numpy(traj).to(device=cam.device, dtype=cam.dtype)
        if cam.dim() == 3:
            cam[w_start:px_end] = vals
        else:
            cam[:, w_start:px_end] = vals.unsqueeze(0).expand(cam.shape[0], -1, -1, -1)
        cache.metadata["cam_c2w"] = cam
        if "cam_c2w_raw" in cache.metadata:
            cache.metadata["cam_c2w_raw"] = cam.clone()
        cache.metadata["frame_end"] = int(cam_frames(cam).shape[0])
        history = cache.history
        pred = pipe.generate(i, cache)
        t1 = time.perf_counter()
        pipe.finalize(i, cache, pred)
        compact(cache)
        overlap = min(DECODE_OVERLAP, int(history.shape[2]))
        latent = torch.cat([history[:, :, -overlap:].contiguous(), pred.to(history.dtype)], dim=2).contiguous()
        decoded = engine.decode_latent_to_video_frames(latent)
        frames = np.ascontiguousarray(decoded[(overlap - 1) * stride + 1:].numpy(), dtype=np.uint8)
        S["ar_index"] = i + 1
        out = []
        for f in frames:
            buf = io.BytesIO(); Image.fromarray(f).save(buf, format="JPEG", quality=req.quality)
            out.append(base64.b64encode(buf.getvalue()).decode())
        t2 = time.perf_counter()
        print(f"[alaya_server] chunk {i + 1}: generate={t1 - t0:.2f}s rest={t2 - t1:.2f}s frames={len(out)} "
              f"fwd={req.forward} yaw={req.yaw}", flush=True)
        return {"frames": out, "chunk": i + 1, "generate_s": round(t1 - t0, 2), "total_s": round(t2 - t0, 2)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", default="configs/infer_pt_352.yaml")
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--compile", default="none")
    a = ap.parse_args()
    load(a.cfg, a.compile)
    print("[alaya_server] model ready", flush=True)
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")
