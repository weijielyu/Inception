"""Build an AlayaWorld "case" (image + camera.pt + prompt [+ skill]) from our own image and a keyboard-style action string.

   .venv_alaya/bin/python scripts/make_alaya_case.py <image> <out_prefix> --actions "w-6,right-3,w-3" \
       --prompt "..." [--skill "..."]
Actions: comma-separated `keys-chunks`; keys are any of w/s (forward/back), a/d (strafe), left/right (yaw),
up/down (pitch), joined with + (e.g. w+right-2), or `idle`. One chunk = 32 frames = 1.33 s at 24 fps.
Uses AlayaWorld's own planner (reactor/alayaworld_camera.py) and motion rates (reactor/alayaworld.yaml), and
borrows the camera intrinsics from the bundled case1, as the upstream reactor demo does for uploaded images.
"""
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

A = Path(__file__).resolve().parent.parent / "third_party/AlayaWorld"
sys.path.insert(0, str(A))
from reactor.alayaworld_camera import MotionConfig, plan_camera_motion  # noqa: E402

CFG = MotionConfig(fps=24.0, strafe_units_per_second=0.126, vertical_units_per_second=0.261,
                   forward_units_per_second=1.905, pitch_degrees_per_second=4.039,
                   yaw_degrees_per_second=9.375, roll_degrees_per_second=4.094)
FRAMES_PER_CHUNK = 32


def parse(actions: str):
    for item in actions.split(","):
        keys, n = item.strip().rsplit("-", 1)
        ks = set(keys.split("+"))
        yield dict(forward=float("w" in ks) - float("s" in ks), strafe=float("d" in ks) - float("a" in ks),
                   yaw=float("right" in ks) - float("left" in ks), pitch=float("up" in ks) - float("down" in ks),
                   vertical=0.0, roll=0.0), int(n)


ap = argparse.ArgumentParser()
ap.add_argument("image"); ap.add_argument("out_prefix")
ap.add_argument("--actions", required=True); ap.add_argument("--prompt", required=True)
ap.add_argument("--skill", default=""); ap.add_argument("--yaw-scale", type=float, default=1.0)
a = ap.parse_args()

tmpl = torch.load(A / "playground/case1/case1_camera.pt", map_location="cpu", weights_only=False)
pose = np.eye(4, dtype=np.float32)
poses = [pose[None]]
chunks = 0
for ctl, n in parse(a.actions):
    ctl["yaw"] *= a.yaw_scale
    seg = plan_camera_motion(pose, frame_count=n * FRAMES_PER_CHUNK, config=CFG, **ctl)
    poses.append(seg); pose = seg[-1]; chunks += n
tail = plan_camera_motion(pose, strafe=0, vertical=0, forward=0, pitch=0, yaw=0, roll=0, frame_count=6 * FRAMES_PER_CHUNK, config=CFG)
c2w = torch.from_numpy(np.concatenate(poses + [tail], axis=0))

out = Path(a.out_prefix); out.parent.mkdir(parents=True, exist_ok=True)
meta = dict(tmpl); meta.update(cam_c2w=c2w, cam_c2w_raw=c2w.clone(), frame_start=0, frame_end=int(c2w.shape[0]), video_id="inception")
torch.save(meta, f"{out}_camera.pt")
shutil.copy(a.image, f"{out}_image{Path(a.image).suffix}")
Path(f"{out}_prompt.txt").write_text(a.prompt)
if a.skill:
    Path(f"{out}_skill.txt").write_text(a.skill)
print(f"case {out}: {chunks} chunks ({chunks*FRAMES_PER_CHUNK/24:.1f}s), {c2w.shape[0]} poses, end t={c2w[chunks*FRAMES_PER_CHUNK][:3,3].tolist()}")
