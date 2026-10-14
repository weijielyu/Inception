"""Scripted end-to-end run: python scripts/run_cli.py <image> "premise" "action 1" "action 2" ..."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from inception.orchestrator import Game  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

image, premise, *actions = sys.argv[1:]
g = Game()
print("SESSION", g.session.root)
print("\n=== OPENING ===\n" + g.start(image, user_premise=premise))
for a in actions:
    v = g.turn(a)
    print(f"\n=== TURN {g.session.state.turn}: {a} ===\n{v.narration}\n[video] {v.video_path}\n[qc] {v.qc_score:.1f} {v.qc_reason} | fallback={v.fallback} | {v.timings}")
