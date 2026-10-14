# Inception — do anything in a generated first-person world (MVP)

A player uploads a scene image, walks with WASD, and types what they want to do. A GM agent
(DeepSeek) rules on the action, rolls dice in code, commits consequences to a structured world
state, narrates, and hands a shot prompt to the renderers. Walking is rendered live by an
autoregressive world model (Matrix-Game 2.0); actions and ambient "idle loops" are rendered as
short Wan2.2 clips and spliced into the stream so the picture never stops. Plot events fire on a
wall clock from the Writer's commitments.

```
text ─► GM (1 LLM call) ─► dice ─► Memory.commit ─► Wan clip ─► Display.enqueue_clip ─┐
keys ─► Display ─► Matrix-Game 2.0 AR stream ───────────────────────────────────────────┼─► WebSocket ─► browser canvas
idle ─► Display ping-pongs a Wan ambient clip ───────────────────────────────────────────┘
```

## Run

```bash
cd ~/Inception
cp .env.example .env           # set keys (file paths) and renderers
.venv/bin/python -m inception.web.server --port 7861
# open http://<host>:7861 — upload an image, click the canvas, WASD to walk, type an action
```

Renderers: `AR_RENDERER=mock|matrixgame2`, `CLIP_RENDERER=mock|wan` (mock = no GPU). GPUs are
auto-picked by free memory (`INCEPTION_GPUS=2,3` to restrict). Model weights live on local NVMe
(`models/ -> /ssd3/wjlyu/inception_models`); sessions (state.json, events.jsonl, stream.mp4) in
`sessions/ -> /ssd3/wjlyu/inception_sessions`. Never put large files in `/home` (200 GB quota).

Headless test: `.venv/bin/python scripts/smoke_ws.py http://127.0.0.1:7861 assets/starters/0000.png`.

Offline evals (no UI): `scripts/gm_eval.py` (GM rulings / narration / shot prompts for a batch of
inputs) and `INCEPTION_GPUS=6 scripts/clip_eval.py` (render those prompts with Wan and score with the
VLM judge). Results and lessons: `docs/eval_results.md`.

Two servers: **7861 = play** (restart only when the user agrees), **7862 = dev** (mock renderers,
`AR_RENDERER=mock CLIP_RENDERER=mock SESSIONS_DIR=/ssd3/wjlyu/inception_sessions/dev`).

## Layout

- `inception/agents/gm.py` — the merged Interact+Prediction+Writer+Prompt call; `roll()` is the dice
- `inception/agents/memory.py`, `inception/state.py` — world state (single source of truth), event log, time-based commitments
- `inception/agents/display.py` — play buffer, source switching (clip > AR > idle), key lock, pixel QC, pre-start, recording
- `inception/agents/qc.py` — pixel gate + async VLM audit (OpenRouter / Anthropic)
- `inception/renderers/` — `matrixgame2.py` (step-wise MG2 with flash-attn→SDPA shim), `wan_clip.py`, `mock.py`
- `inception/orchestrator.py` — `Game`: start / act / idle regen / plot tick
- `inception/web/` — FastAPI + WebSocket server and the single-page client
- `scripts/spike_*.py` — renderer benchmarks (see `docs/spike_results.md`)
- `research_notes/`, `reports/` — the market/tech research this design is based on

Legacy split agents (`agents/interact.py`, `prediction.py`, `prompt.py`, `writer.py` narration) and
the Gradio `app.py` / HTTP `film_server.py` are kept for reference but are off the critical path.
