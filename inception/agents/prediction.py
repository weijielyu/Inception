"""Prediction agent: decides what actually happens, as a structured state delta.

Success/failure is resolved in CODE (seeded dice) before the LLM sees anything, so that the
narrator cannot be sycophantic. The LLM only fills in plausible consequences and hidden truths
(what is under the ground), which are then committed to memory and never contradicted.
"""
from __future__ import annotations

import random

from pydantic import BaseModel, Field

from ..state import Entity
from .base import Agent
from .interact import Intent


class StateDelta(BaseModel):
    entities_added: list[Entity] = Field(default_factory=list)
    entities_removed: list[str] = Field(default_factory=list, description="names of entities that no longer exist")
    entities_updated: list[Entity] = Field(default_factory=list, description="entities whose state/where/hidden changed; match by name")
    player_position: str = Field(default="", description="new position, or empty for unchanged")
    inventory_add: list[str] = Field(default_factory=list)
    inventory_remove: list[str] = Field(default_factory=list)
    health_change: int = 0
    status_add: list[str] = Field(default_factory=list)
    status_remove: list[str] = Field(default_factory=list)
    new_facts: list[str] = Field(default_factory=list, description="new permanent facts about the world revealed by this action")
    flags: dict[str, str] = Field(default_factory=dict)


class Outcome(BaseModel):
    success: bool
    visible_result: str = Field(description="1-2 sentences: what the player SEES happen, first person, present tense")
    delta: StateDelta


SYSTEM = """You are the PREDICTION agent — the physics and consequence engine of a first-person adventure. You are told the player's intent and whether it SUCCEEDED or FAILED (already decided by dice; do not change it). Produce the concrete consequences as a state delta.

Guidelines:
- Be concrete and physical. Consequences should be plausible for this scene and consistent with all committed FACTS and ENTITIES (including HIDDEN ones — reveal them if the action would uncover them).
- When the action probes the unknown (digging, opening, searching) and no hidden entity exists there yet, you may invent what is found, but keep it proportionate: most digging finds dirt, roots, stones; interesting finds should be rare (roughly 1 in 4) and small. Record whatever you invent as new entities/facts so it stays true forever.
- Failure should have texture: partial progress, a cost (tiredness, a broken tool, noise that attracts attention), not just "nothing happens".
- Never narrate; `visible_result` is a plain factual description used to render video."""


class PredictionAgent(Agent):
    name = "prediction"

    def roll(self, intent: Intent, seed: int | None = None) -> tuple[bool, int | None]:
        if intent.ruling == "allowed":
            return True, None
        if intent.ruling == "denied":
            return False, None
        rng = random.Random(seed)
        r = rng.randint(1, 20)
        return r >= 2 * intent.difficulty - 1, r  # d20 vs difficulty-derived DC

    def run(self, intent: Intent, success: bool, roll: int | None) -> Outcome:
        verdict = "SUCCEEDED" if success else "FAILED"
        if intent.ruling == "denied":
            verdict = "IS IMPOSSIBLE (the player tries and visibly cannot)"
        user = (
            f"WORLD STATE:\n{self.session.state.summary_for_llm()}\n\n"
            f"INTENT: {intent.model_dump_json()}\nDICE: {roll}\nTHE ATTEMPT {verdict}.\n"
            "Return the Outcome with success set accordingly."
        )
        out = self.llm.json(SYSTEM, user, Outcome)
        out.success = success  # code is the authority
        self.emit("outcome", roll=roll, outcome=out.model_dump())
        return out
