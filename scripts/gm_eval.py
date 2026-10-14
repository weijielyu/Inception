"""Offline GM-prompt eval: run the merged GM call on a batch of player inputs against a fixed
world state and print rulings, dice, narration and the shot prompt. No video, no server.

   python scripts/gm_eval.py [--state sessions/<id>/state.json] [--inputs file.txt]
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from inception.agents.gm import GMAgent  # noqa: E402
from inception.llm import LLM  # noqa: E402
from inception.state import Scene, Session, WorldState  # noqa: E402

DEFAULT_INPUTS = [
    "我要开始挖地",
    "There is an elephant on the road",
    "这是哪里？附近有人吗？",
    "我爬上最近的那棵树看看远处",
    "我把背包里的东西都倒出来",
    "召唤一条龙把这里烧了",
    "It starts to rain heavily",
    "我大声喊：有人吗！",
]

ap = argparse.ArgumentParser()
ap.add_argument("--state", default=None, help="state.json of an existing session (default: a synthetic forest scene)")
ap.add_argument("--inputs", default=None, help="text file, one input per line")
ap.add_argument("--out", default="logs/gm_eval.jsonl")
a = ap.parse_args()

root = Path("/ssd3/wjlyu/inception_sessions/eval") / time.strftime("gm-%H%M%S")
session = Session(root)
if a.state:
    session.state = WorldState.model_validate_json(Path(a.state).read_text())
else:
    session.state = WorldState(
        scene=Scene(description="A dirt path leads into a dense spring forest; grass and young trees on both sides, dappled sunlight.",
                    style="photorealistic, natural light, 35mm lens, muted palette", location="forest path", time_of_day="morning"),
        premise="You came here following a letter that says your sister is alive.",
        facts=["[hidden truth] An old brass compass is buried beside the third tree on the left."],
        started_at=time.time() - 60,
    )
inputs = [l.strip() for l in Path(a.inputs).read_text().splitlines() if l.strip()] if a.inputs else DEFAULT_INPUTS

gm = GMAgent(LLM(), session)
rows = []
for i, text in enumerate(inputs, 1):
    t0 = time.time()
    try:
        res = gm.run(text)
        ok, roll = gm.roll(res, i)
        b = res.success if ok else res.failure
        row = {"input": text, "kind": res.kind, "verb": res.verb, "ruling": res.ruling, "difficulty": res.difficulty,
               "roll": roll, "success": ok, "reason": res.reason, "visible": b.visible_result, "narration": b.narration,
               "clip_prompt": b.clip_prompt, "expected": b.expected_visible, "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        row = {"input": text, "error": str(e)[:300], "seconds": round(time.time() - t0, 1)}
    rows.append(row)
    print(f"\n[{i}] {text}  ({row['seconds']}s)")
    if "error" in row:
        print("   ERROR", row["error"]); continue
    print(f"   kind={row['kind']} verb={row['verb']} ruling={row['ruling']} diff={row['difficulty']} roll={row['roll']} -> {'success' if ok else 'FAIL'} | {row['reason']}")
    print(f"   visible : {row['visible']}")
    print(f"   narr    : {row['narration']}")
    print(f"   prompt  : {row['clip_prompt']}")
    print(f"   expect  : {row['expected']}")
Path(a.out).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
print(f"\nwrote {a.out}; session dir {root}")
