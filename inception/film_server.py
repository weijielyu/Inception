"""GPU worker: loads Wan 2.2 TI2V-5B once (DiffSynth) and serves image-to-video over HTTP.

    CUDA_VISIBLE_DEVICES=2 python -m inception.film_server --port 8765
"""
from __future__ import annotations

import argparse
import base64
import io
import logging
import time
from pathlib import Path

import torch
import uvicorn
from fastapi import FastAPI
from PIL import Image
from pydantic import BaseModel

from .config import settings

log = logging.getLogger("inception.film_server")
app = FastAPI(title="Inception film server")
PIPE = None

NEG_DEFAULT = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，"
               "JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，"
               "手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走")


class GenRequest(BaseModel):
    image_b64: str
    prompt: str
    negative_prompt: str = ""
    width: int = 832
    height: int = 480
    num_frames: int = 81
    fps: int = 16
    steps: int = 30
    seed: int = 0
    out_path: str


def load_pipeline(model_dir: str):
    from diffsynth.pipelines.wan_video import ModelConfig, WanVideoPipeline

    d = Path(model_dir)
    pipe = WanVideoPipeline.from_pretrained(
        torch_dtype=torch.bfloat16,
        device="cuda",
        model_configs=[
            ModelConfig(path=str(d / "models_t5_umt5-xxl-enc-bf16.pth")),
            ModelConfig(path=sorted(str(p) for p in d.glob("diffusion_pytorch_model*.safetensors"))),
            ModelConfig(path=str(d / "Wan2.2_VAE.pth")),
        ],
        tokenizer_config=ModelConfig(path=str(d / "google/umt5-xxl")),
    )
    return pipe


@app.on_event("startup")
def _startup():
    global PIPE
    t0 = time.time()
    PIPE = load_pipeline(settings.wan_model_dir)
    log.info("pipeline loaded in %.0fs", time.time() - t0)


@app.get("/health")
def health():
    return {"ok": PIPE is not None, "model": settings.wan_model_dir}


@app.post("/generate")
def generate(req: GenRequest):
    from diffsynth.utils.data import save_video

    img = Image.open(io.BytesIO(base64.b64decode(req.image_b64))).convert("RGB").resize((req.width, req.height))
    t0 = time.time()
    video = PIPE(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt or NEG_DEFAULT,
        input_image=img,
        seed=req.seed,
        tiled=True,
        height=req.height,
        width=req.width,
        num_frames=req.num_frames,
        num_inference_steps=req.steps,
    )
    out = Path(req.out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_video(video, str(out), fps=req.fps, quality=5)
    dt = time.time() - t0
    log.info("generated %s in %.1fs", out, dt)
    return {"video_path": str(out), "seconds": dt}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    uvicorn.run(app, host=a.host, port=a.port)
