"""Gradio UI: upload a scene, type what you do, watch the clip, inspect the agents' log."""
from __future__ import annotations

import json
import logging

import gradio as gr

from .orchestrator import Game

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
GAMES: dict[str, Game] = {}


def _events_md(game: Game, n: int = 25) -> str:
    rows = []
    for e in game.session.events(n):
        payload = {k: v for k, v in e.items() if k not in ("ts", "turn", "agent", "event")}
        rows.append(f"- **t{e['turn']} {e['agent']}** · {e['event']} · `{json.dumps(payload, ensure_ascii=False)[:300]}`")
    return "\n".join(rows) or "(no events)"


def start(image, premise, session_state):
    if image is None:
        raise gr.Error("Upload a scene image first.")
    game = Game()
    opening = game.start(image, user_premise=premise or "")
    GAMES[game.session_id] = game
    return (game.session_id, opening, None, str(game.current_frame),
            game.session.state.model_dump_json(indent=2, ensure_ascii=False), _events_md(game))


def act(action, session_id):
    game = GAMES.get(session_id)
    if game is None:
        raise gr.Error("Start a game first.")
    if not action or not action.strip():
        raise gr.Error("Type what you want to do.")
    view = game.turn(action.strip())
    status = f"QC {view.qc_score:.1f} ({view.qc_reason}) · fallback: {view.fallback} · timings {view.timings}"
    return (view.narration + f"\n\n_{status}_", str(view.video_path) if view.video_path else None,
            str(view.current_frame), game.session.state.model_dump_json(indent=2, ensure_ascii=False), _events_md(game))


with gr.Blocks(title="Inception") as demo:
    gr.Markdown("# Inception — do anything in a generated world (MVP)")
    sid = gr.State("")
    with gr.Row():
        with gr.Column(scale=1):
            image = gr.Image(type="filepath", label="Seed scene")
            premise = gr.Textbox(label="Optional premise / what you want this world to be")
            start_btn = gr.Button("Start world", variant="primary")
            action = gr.Textbox(label="What do you do?", placeholder="我要开始挖地")
            act_btn = gr.Button("Do it")
        with gr.Column(scale=2):
            video = gr.Video(label="What you see", autoplay=True)
            narration = gr.Markdown()
            frame = gr.Image(label="Current frame (next clip starts here)", type="filepath")
    with gr.Accordion("World state (Memory agent)", open=False):
        state_box = gr.Code(language="json")
    with gr.Accordion("Agent event log", open=False):
        events = gr.Markdown()
    start_btn.click(start, [image, premise, sid], [sid, narration, video, frame, state_box, events])
    act_btn.click(act, [action, sid], [narration, video, frame, state_box, events])
    action.submit(act, [action, sid], [narration, video, frame, state_box, events])

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
