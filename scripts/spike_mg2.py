"""Spike: Matrix-Game 2.0 as a step-wise renderer. Measures load time, s/block, fps, VRAM.
   python scripts/spike_mg2.py <image> <out.mp4> [--blocks 20]"""
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
from inception.renderers.base import Keys  # noqa: E402
from inception.renderers.matrixgame2 import MatrixGame2Walk  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
ap = argparse.ArgumentParser()
ap.add_argument("image"); ap.add_argument("out"); ap.add_argument("--blocks", type=int, default=20)
ap.add_argument("--device", default=None)
a = ap.parse_args()

t0 = time.time()
r = MatrixGame2Walk(device=a.device)
print(f"LOAD {time.time()-t0:.0f}s  VRAM {torch.cuda.max_memory_allocated(r.device)/1e9:.1f} GB")

img = Image.open(a.image).convert("RGB")
# resize-crop to 640x352 like upstream
w, h = img.size
if h / w > 352 / 640:
    nh = int(w * 352 / 640); img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
else:
    nw = int(h * 640 / 352); img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
frame = np.asarray(img.resize((640, 352)))

t0 = time.time(); r.start(frame); print(f"START {time.time()-t0:.1f}s")
script = [Keys(w=True)] * 8 + [Keys(w=True, dx=10)] * 4 + [Keys(d=True)] * 4 + [Keys()] * 2 + [Keys(a=True, dx=-10)] * 4
script = (script * 10)[: a.blocks]
frames, times = [], []
for i, k in enumerate(script):
    t1 = time.time(); out = r.step(k); dt = time.time() - t1
    times.append(dt); frames.extend(out)
    print(f"block {i:02d} keys w{int(k.w)}a{int(k.a)}s{int(k.s)}d{int(k.d)} dx{k.dx:+.0f}: {len(out)} frames in {dt:.2f}s -> {len(out)/dt:.1f} fps")
iio.imwrite(a.out, np.stack(frames), fps=16, codec="libx264", plugin="pyav")
print(f"TOTAL {len(frames)} frames, mean {np.mean(times[1:]):.2f}s/block, {len(frames)/sum(times):.1f} fps generated, "
      f"VRAM peak {torch.cuda.max_memory_allocated(r.device)/1e9:.1f} GB -> {a.out}")
