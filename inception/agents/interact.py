"""Interact agent: free-form player input -> typed intent + ruling.

Policy (from the research): never hard-deny. Return allowed / conditional / denied, always
with an in-world reason; `conditional` means the outcome is uncertain and must be rolled.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .base import Agent


class Intent(BaseModel):
    verb: str = Field(description="canonical verb, e.g. dig, walk, pick_up, talk, attack, look, wait")
    target: str = Field(default="", description="what the verb acts on, or empty")
    instrument: str = Field(default="", description="tool/means used, or empty")
    manner: str = Field(default="", description="how: carefully, quickly, with bare hands ...")
    ruling: Literal["allowed", "conditional", "denied"]
    difficulty: int = Field(default=5, ge=1, le=10, description="1 trivial .. 10 nearly impossible; only matters if conditional")
    reason: str = Field(description="one in-world sentence explaining the ruling")
    normalized: str = Field(description="short canonical phrasing of the action, e.g. 'dig the ground with bare hands'")


SYSTEM = """You are the INTERACT agent of a generative first-person adventure. The player types what they want to do in free text (possibly Chinese or English). Convert it into ONE typed intent and rule on it.

Rules:
- The player can attempt almost anything physically imaginable for a human in this scene. Prefer `allowed` for trivial acts (walk, look, touch, pick up small things) and `conditional` for anything with uncertain outcome (digging, climbing, fighting, persuading, searching). Use `denied` ONLY for things that are impossible in this world (teleporting, summoning objects from nothing, controlling other characters' minds) and give an in-world reason, never a meta one.
- Respect the committed world state: if the player references something that does not exist, treat the action as attempting it anyway (they may be mistaken) rather than denying.
- Keep `normalized` short and in English; it is used as a cache key."""


class InteractAgent(Agent):
    name = "interact"

    def run(self, player_text: str) -> Intent:
        user = f"WORLD STATE:\n{self.session.state.summary_for_llm()}\n\nPLAYER SAYS: {player_text}"
        intent = self.llm.json(SYSTEM, user, Intent)
        self.emit("intent", text=player_text, intent=intent.model_dump())
        return intent
