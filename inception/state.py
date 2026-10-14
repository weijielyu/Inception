"""World state — the single source of truth. Video is only a renderer of this.

Deliberately simple: a JSON document on disk plus an append-only event log. Agents never
mutate it directly; they propose deltas that the Memory agent validates and commits.
Thread-safe (Display loop, GM worker and renderer threads all touch it) and written atomically.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Scene(BaseModel):
    description: str = ""          # what the seed image shows (VLM caption or user text)
    style: str = ""                # immutable style block attached to every video prompt
    location: str = ""
    time_of_day: str = "day"
    weather: str = "clear"


class Player(BaseModel):
    position: str = "standing in the scene"
    inventory: list[str] = Field(default_factory=list)
    status: list[str] = Field(default_factory=list)   # e.g. "tired", "injured"
    health: int = 10


class Entity(BaseModel):
    name: str
    kind: str = "object"           # object | npc | creature | terrain
    state: str = ""
    where: str = ""
    hidden: bool = False           # exists in truth but not yet seen by the player


class Commitment(BaseModel):
    """A promise the Writer made to the plot: fire `event` once `trigger_seconds` of play elapsed."""
    trigger_seconds: float = Field(description="seconds after the world starts (wall clock)")
    event: str
    fired: bool = False


class HistoryEntry(BaseModel):
    turn: int
    action: str
    outcome: str
    narration: str


class WorldState(BaseModel):
    scene: Scene = Field(default_factory=Scene)
    player: Player = Field(default_factory=Player)
    entities: list[Entity] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)    # committed world facts, never contradicted
    flags: dict[str, Any] = Field(default_factory=dict)
    turn: int = 0
    started_at: float = 0.0                           # wall clock of /start
    premise: str = ""
    commitments: list[Commitment] = Field(default_factory=list)
    history: list[HistoryEntry] = Field(default_factory=list)

    # -------------------------------------------------------------- helpers
    def elapsed(self) -> float:
        return time.time() - self.started_at if self.started_at else 0.0

    def summary_for_llm(self, max_history: int = 6) -> str:
        """Compact context block handed to every agent."""
        ents = "\n".join(
            f"- {e.name} ({e.kind}{', HIDDEN' if e.hidden else ''}): {e.state} @ {e.where}" for e in self.entities
        ) or "- (none)"
        hist = "\n".join(
            f"[t{h.turn}] player: {h.action} -> {h.outcome}" for h in self.history[-max_history:]
        ) or "(nothing yet)"
        facts = "\n".join(f"- {f}" for f in self.facts[-20:]) or "- (none)"
        return (
            f"TURN: {self.turn}  (elapsed {self.elapsed():.0f}s)\nPREMISE: {self.premise}\n"
            f"SCENE: {self.scene.description}\nLOCATION: {self.scene.location}; {self.scene.time_of_day}, {self.scene.weather}\n"
            f"STYLE: {self.scene.style}\n"
            f"PLAYER: {self.player.position}; health {self.player.health}; inventory {self.player.inventory}; status {self.player.status}\n"
            f"ENTITIES:\n{ents}\nFACTS:\n{facts}\nFLAGS: {json.dumps(self.flags, ensure_ascii=False)}\n"
            f"RECENT HISTORY:\n{hist}"
        )


class Session:
    """On-disk container for one play session: state.json, events.jsonl, clips/, frames/."""

    def __init__(self, root: Path):
        self.root = root
        self.clips = root / "clips"
        self.frames = root / "frames"
        for d in (self.root, self.clips, self.frames):
            d.mkdir(parents=True, exist_ok=True)
        self.state_path = root / "state.json"
        self.events_path = root / "events.jsonl"
        self.lock = threading.RLock()
        self.state = WorldState()
        if self.state_path.exists():
            self.state = WorldState.model_validate_json(self.state_path.read_text())

    def save(self) -> None:
        with self.lock:
            tmp = self.state_path.with_suffix(".json.tmp")
            tmp.write_text(self.state.model_dump_json(indent=2, ensure_ascii=False))
            os.replace(tmp, self.state_path)

    def log(self, agent: str, event: str, **payload: Any) -> None:
        rec = {"ts": time.time(), "turn": self.state.turn, "agent": agent, "event": event, **payload}
        with self.lock:
            with self.events_path.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    def events(self, last: int = 50) -> list[dict]:
        if not self.events_path.exists():
            return []
        lines = self.events_path.read_text().splitlines()[-last:]
        return [json.loads(l) for l in lines]
