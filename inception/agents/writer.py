"""Writer agent: narrator + plot director.

It only narrates outcomes it is handed (it cannot change them), and it advances the main
plot through explicit commitments ("a beast arrives on turn 4") that Memory tracks, so plot
beats are deliberate rather than improvised each turn.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..state import Commitment
from .base import Agent
from .interact import Intent
from .prediction import Outcome


class Narration(BaseModel):
    narration: str = Field(description="2-4 sentences of second-person present-tense narration of exactly what happened; vivid but faithful")
    plot_event_visible: str = Field(default="", description="if a due plot event happens now, a plain visual description of it for the video; else empty")
    new_commitments: list[Commitment] = Field(default_factory=list, description="optional future plot beats to schedule (trigger_seconds must be later than now)")


class Setup(BaseModel):
    premise: str = Field(description="2-3 sentence premise for this world, grounded in the scene")
    style: str = Field(description="one line of visual style keywords applied to every video prompt (lighting, lens, palette, realism)")
    location: str
    time_of_day: str
    commitments: list[Commitment] = Field(description="2-3 scheduled plot beats with trigger_seconds between 30 and 240, e.g. distant growl at 45s, creature appears at 120s")
    hidden_truths: list[str] = Field(description="2-4 secret facts about the scene the player may discover (what is buried, who lives here)")


SYSTEM = """You are the WRITER agent of a first-person generative adventure: a narrator and a quiet plot director.

Hard rules:
- Narrate ONLY the outcome you are given. Never add results, items or successes that are not in the Outcome. Never contradict FACTS.
- Keep it short (2-4 sentences), sensory, second person, present tense. Match the language the player writes in.
- If DUE PLOT EVENTS are listed, weave exactly those into the narration and describe them visually in plot_event_visible. Otherwise leave it empty.
- You may schedule new plot beats (new_commitments) when the story needs tension, 2-5 turns ahead. Do not schedule more than one per turn."""

SETUP_SYSTEM = """You are the WRITER agent setting up a new first-person generative adventure from a seed scene. Ground everything in the scene description; propose a premise with stakes, a fixed visual style line, 2-3 scheduled plot beats (trigger_seconds 30-240 of wall-clock play, escalating), and a few hidden truths the player may uncover (these become secret world facts).

TONE: follow the requested tone exactly. If the tone is calm/exploration, plot beats are gentle and curious (weather, an animal passing, a discovery, a traveller) — no horror, monsters, gore or dread unless the tone asks for it. Plot beats must be concrete, unmistakable on camera within 4 seconds (someone or something ARRIVES, APPEARS, CHANGES the scene), never subtle hints like a petal moving or a faint hum."""


class WriterAgent(Agent):
    name = "writer"

    def setup(self, scene_description: str, user_premise: str, tone: str = "calm exploration") -> Setup:
        user = f"SCENE (from the seed image): {scene_description}\nTONE: {tone}\nPLAYER'S OWN PREMISE (may be empty): {user_premise}"
        s = self.llm.json(SETUP_SYSTEM, user, Setup)
        self.emit("setup", setup=s.model_dump())
        return s

    def run(self, player_text: str, intent: Intent, outcome: Outcome, due_events: list[str]) -> Narration:
        user = (
            f"WORLD STATE:\n{self.session.state.summary_for_llm()}\n\n"
            f"PLAYER SAID: {player_text}\nINTENT: {intent.normalized} (ruling {intent.ruling}: {intent.reason})\n"
            f"OUTCOME (success={outcome.success}): {outcome.visible_result}\n"
            f"DUE PLOT EVENTS NOW: {due_events or 'none'}"
        )
        n = self.llm.json(SYSTEM, user, Narration)
        n.new_commitments = [c for c in n.new_commitments if c.trigger_seconds > self.session.state.elapsed()]
        self.emit("narration", narration=n.model_dump())
        return n
