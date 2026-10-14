"""Spike: "walking" with a bidirectional clip model by chaining short camera-motion clips.
Each clip starts from the previous clip's last frame. Measures seconds per clip and saves the chain.
   python scripts/spike_bidir_walk.py <image> <out.mp4> [--clips 8] [--frames 33] [--steps 8]"""
import argparse
import logging
import sys
import time
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from inception.renderers.wan_clip import WanClip  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
ap = argparse.ArgumentParser()
ap.add_argument("image"); ap.add_argument("out")
ap.add_argument("--clips", type=int, default=8); ap.add_argument("--frames", type=int, default=33)
ap.add_argument("--steps", type=int, default=8); ap.add_argument("--device", default=None)
a = ap.parse_args()

MOVES = {
    "forward": "The camera walks slowly forward along the path, steady first-person view, smooth continuous motion",
    "left": "The camera turns smoothly to the left while standing still, first-person view, smooth continuous pan",
    "right": "The camera turns smoothly to the right while standing still, first-person view, smooth continuous pan",
}
plan = ["forward", "forward", "forward", "right", "right", "forward", "left", "forward", "forward", "forward"][: a.clips]
style = "photorealistic, natural light, consistent scene, no cuts, no text"

r = WanClip(640, 352, 16, steps=a.steps, device=a.device)
frame = np.asarray(Image.open(a.image).convert("RGB").resize((640, 352)))
chain, times = [], []
for i, mv in enumerate(plan):
    t0 = time.time()
    frames = r.render(frame, f"{MOVES[mv]}. {style}", (a.frames - 1) / 16, seed=i, steps=a.steps)
    dt = time.time() - t0
    times.append(dt)
    chain.extend(frames)
    frame = frames[-1]
    print(f"clip {i} {mv:7s}: {len(frames)} frames in {dt:.1f}s", flush=True)
iio.imwrite(a.out, np.stack(chain), fps=16, codec="libx264", plugin="pyav")
print(f"TOTAL {len(chain)} frames ({len(chain)/16:.0f}s of video), mean {np.mean(times[1:]):.1f}s/clip, "
      f"VRAM {torch.cuda.max_memory_allocated(r.device)/1e9:.1f} GB -> {a.out}")
