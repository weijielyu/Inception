"""Cache agent (speculative pre-generation). MVP scope: after each turn, guess the top-k
likely next actions and pre-render them in a background thread; a later turn whose
normalized intent matches exactly reuses the clip. Disabled by default (CACHE_ENABLED=1)."""
from __future__ import annotations

import threading
from pathlib import Path

from pydantic import BaseModel, Field

from ..config import settings
from .base import Agent


class Guesses(BaseModel):
    actions: list[str] = Field(description="most likely next player actions, short English phrases, most likely first")


SYSTEM = "You are the CACHE agent. Given the world state and the last narration, guess what the player will most likely try next."


class CacheAgent(Agent):
    name = "cache"

    def __init__(self, llm, session):
        super().__init__(llm, session)
        self.store: dict[str, Path] = {}
        self.lock = threading.Lock()

    def guess(self, last_narration: str) -> list[str]:
        user = f"WORLD STATE:\n{self.session.state.summary_for_llm()}\n\nLAST NARRATION: {last_narration}\nReturn {settings.cache_top_k} guesses."
        g = self.llm.json(SYSTEM, user, Guesses)
        self.emit("guesses", actions=g.actions)
        return g.actions[: settings.cache_top_k]

    def key(self, turn: int, normalized: str) -> str:
        return f"{turn}:{normalized.strip().lower()}"

    def put(self, key: str, path: Path) -> None:
        with self.lock:
            self.store[key] = path

    def get(self, key: str) -> Path | None:
        with self.lock:
            return self.store.get(key)
