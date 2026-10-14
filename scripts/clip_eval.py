"""Offline clip eval: render (start frame, prompt) pairs with the Wan clip renderer and score them
with the VLM judge — measures whether our shot prompts produce the right video.

   INCEPTION_GPUS=6 python scripts/clip_eval.py [--cases logs/gm_eval.jsonl] [--image assets/starters/0000.png] [--seeds 1]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from inception.agents.qc import SYSTEM as QC_SYSTEM, Verdict  # noqa: E402
from inception.llm import VLM  # noqa: E402
from inception.renderers.wan_clip import WanClip  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cases", default="logs/gm_eval.jsonl", help="jsonl with clip_prompt + expected (from gm_eval.py)")
ap.add_argument("--image", default="assets/starters/0000.png")
ap.add_argument("--seeds", type=int, default=1)
ap.add_argument("--steps", type=int, default=25)
ap.add_argument("--seconds", type=float, default=4)
ap.add_argument("--limit", type=int, default=6)
ap.add_argument("--size", default="640x352", help="WxH, e.g. 832x480")
ap.add_argument("--out", default="/ssd3/wjlyu/inception_sessions/eval/clips")
a = ap.parse_args()
out = Path(a.out) / time.strftime("%H%M%S"); out.mkdir(parents=True, exist_ok=True)

cases = [json.loads(l) for l in Path(a.cases).read_text().splitlines() if l.strip()]
cases = [c for c in cases if c.get("clip_prompt")][: a.limit]
W, H = (int(v) for v in a.size.lower().split("x"))
frame = np.asarray(Image.open(a.image).convert("RGB").resize((W, H)))
start_path = out / "start.jpg"; Image.fromarray(frame).save(start_path, quality=90)
r = WanClip(W, H, 16, steps=a.steps)
vlm = VLM()
rows = []
for i, c in enumerate(cases):
    for seed in range(a.seeds):
        t0 = time.time()
        frames = r.render(frame, c["clip_prompt"], a.seconds, seed=seed)
        dt = time.time() - t0
        p = out / f"case{i}_seed{seed}.mp4"
        iio.imwrite(p, np.stack(frames), fps=16, codec="libx264", plugin="pyav")
        score, verdict = None, None
        if vlm.available:
            n = len(frames); paths = [start_path]
            for k in range(4):
                q = out / f"case{i}_seed{seed}_f{k}.jpg"
                Image.fromarray(frames[min(n - 1, int(n * k / 4 + n / 8))]).save(q, quality=85); paths.append(q)
            try:
                v = vlm.json(QC_SYSTEM, "EXPECTED VISIBLE RESULTS: " + "; ".join(c["expected"]) +
                             "\nFirst image is the START FRAME; the next 4 are sampled from the clip in order.", paths, Verdict)
                score = round(0.4 * v.scene_continuity + 0.35 * v.action_match + 0.25 * v.artifact_free, 2); verdict = v.model_dump()
            except Exception as e:
                verdict = {"error": str(e)[:200]}
        rows.append({"case": i, "seed": seed, "input": c["input"], "prompt": c["clip_prompt"], "expected": c["expected"],
                     "seconds": round(dt, 1), "score": score, "verdict": verdict, "video": str(p)})
        print(f"case {i} seed {seed} [{dt:.0f}s] score={score} | {c['input']} | {verdict and verdict.get('reason', verdict)}")
(out / "results.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows))
scores = [x["score"] for x in rows if x["score"] is not None]
print(f"\nmean score {np.mean(scores):.2f} over {len(scores)} clips -> {out}")
if a.seeds > 1:   # experiment (b): best-of-N by judge score
    best = {}
    for x in rows:
        if x["score"] is not None:
            best[x["case"]] = max(best.get(x["case"], -1), x["score"])
    single = [x["score"] for x in rows if x["seed"] == 0 and x["score"] is not None]
    print(f"best-of-{a.seeds} mean {np.mean(list(best.values())):.2f} vs seed-0 mean {np.mean(single):.2f}")
