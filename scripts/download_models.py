"""Sequentially fetch the candidate open video models into ./models (resumable)."""
import sys
from huggingface_hub import snapshot_download

ROOT = "/home/wjlyu/Inception/models"
JOBS = [
    ("Skywork/Matrix-Game-2.0", None, None),
    ("Skywork/Matrix-Game-3.0", None, None),
    ("tencent/HY-WorldPlay", None, ["bidirectional_model/*", "ar_model/*", "ar_rl_model/*"]),
]
only = sys.argv[1:]  # optional subset by repo id
for repo, allow, ignore in JOBS:
    if only and repo not in only:
        continue
    print("=== downloading", repo, flush=True)
    p = snapshot_download(repo, local_dir=f"{ROOT}/{repo}", allow_patterns=allow, ignore_patterns=ignore, max_workers=8)
    print("=== DONE", repo, p, flush=True)
