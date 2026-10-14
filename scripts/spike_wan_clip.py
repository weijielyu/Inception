"""Spike: Wan2.2 TI2V-5B clip timing at the display resolution.
   python scripts/spike_wan_clip.py <image> <out_dir> [--steps 25] [--frames 65]"""
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
from inception.agents.gm import GMAgent  # noqa: E402
from inception.renderers.wan_clip import WanClip  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
ap = argparse.ArgumentParser()
ap.add_argument("image"); ap.add_argument("out_dir")
ap.add_argument("--steps", type=int, default=25); ap.add_argument("--frames", type=int, default=65)
ap.add_argument("--device", default=None)
a = ap.parse_args()
out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

t0 = time.time()
r = WanClip(640, 352, 16, steps=a.steps, device=a.device)
print(f"LOAD {time.time()-t0:.0f}s")
frame = np.asarray(Image.open(a.image).convert("RGB").resize((640, 352)))
style = "photorealistic, natural light, 35mm lens, muted palette"
tests = {
    "idle": GMAgent.idle_prompt("a quiet scene as seen from where the viewer stands", style),
    "dig": "First-person POV. My own two hands reach down and dig into the ground in front of me, scooping soil aside; "
           "dirt flies, a shallow hole forms and the corner of an old wooden box appears. Camera steady, no cuts. " + style,
}
sec = (a.frames - 1) / 16
for name, prompt in tests.items():
    t1 = time.time()
    frames = r.render(frame, prompt, sec, seed=1)
    dt = time.time() - t1
    iio.imwrite(out / f"wan_{name}_{a.steps}steps.mp4", np.stack(frames), fps=16, codec="libx264", plugin="pyav")
    print(f"{name}: {len(frames)} frames, {dt:.1f}s ({dt/len(frames):.2f} s/frame), VRAM peak {torch.cuda.max_memory_allocated(r.device)/1e9:.1f} GB")
