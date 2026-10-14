"""GM agent — the one LLM call per player action (merges Interact + Prediction + Writer + Prompt).

It returns a ruling plus BOTH a success and a failure branch; code rolls the dice afterwards
and commits exactly one branch, so the model can never decide that the player succeeds.
"""
from __future__ import annotations

import random
import zlib
from typing import Literal

from pydantic import BaseModel, Field

from ..config import settings
from .base import Agent
from .prediction import StateDelta


class Branch(BaseModel):
    delta: StateDelta
    visible_result: str = Field(description="1-2 plain sentences of what the player SEES happen (used for video)")
    narration: str = Field(description="2-3 sentences, second person present tense, in the configured narration language; faithful to visible_result")
    clip_prompt: str = Field(description="<=70 words image-to-video prompt: first-person POV, continuous from the current frame, describes the visible motion/result over ~4 s; no text overlays, no cuts; ends with the STYLE line")
    expected_visible: list[str] = Field(description="2-3 short things a judge should see in the clip")


class GMResult(BaseModel):
    kind: Literal["action", "declare", "question"] = Field(description="action = the player does something; declare = the player states something about the world (director mode, e.g. 'there is an elephant on the road'); question = asks about the world")
    verb: str = Field(description="canonical verb: dig, walk, pick_up, open, talk, attack, look, wait ...")
    target: str = ""
    normalized: str = Field(description="short canonical English phrasing of the action")
    ruling: Literal["allowed", "conditional", "denied"]
    difficulty: int = Field(default=5, ge=1, le=10, description="only matters when conditional: 1 trivial .. 10 nearly impossible")
    reason: str = Field(description="one in-world sentence explaining the ruling")
    success: Branch
    failure: Branch = Field(description="for ruling=denied, describe the visible futility; for allowed, a mild complication variant")


SYSTEM = """You are the GAME MASTER of a first-person generative adventure. The player types what they want to do (any language). In ONE answer you must: interpret it, rule on it, and prepare BOTH possible outcomes. The engine rolls dice afterwards and keeps exactly one branch — you never decide success.

Ruling policy: `allowed` for trivial acts (walk, look, touch, pick up small things); `conditional` for anything uncertain (digging, climbing, fighting, persuading, searching) with a difficulty 1-10; `denied` ONLY for the physically impossible in this world (teleporting, conjuring objects, mind control) with an in-world reason — never a meta one. Never hard-refuse: a denied action still visibly happens as a futile attempt.

Consequences (state deltas): be concrete and physical, consistent with FACTS and ENTITIES (reveal HIDDEN ones if the action would uncover them). Probing the unknown (digging, opening, searching) usually finds mundane things; interesting finds are rare (~1 in 4) and small. Anything you invent becomes a permanent fact — record it. Failure has texture (partial progress, a cost, noise that draws attention), never "nothing happens".

Narration: short, sensory, second person, present tense, written in {LANG} regardless of the input language; narrate only the branch's own outcome.

Video prompt (this feeds a small image-to-video model, so write for what it can do):
- Start by restating the CURRENT VIEW in a few words, then describe ONE clear visible change over ~4 seconds.
- Prefer RESULT + CAMERA over hand choreography: say what appears, moves, opens or changes in the scene ("a shallow hole opens in the dirt in front of the camera, the corner of a wooden box shows") rather than "hands dig and scoop". Mention hands at most once, as a small detail, never as the main subject.
- Things entering the frame (an animal walks in, a person approaches, a door opens, fog rolls in) are reliable; fine finger work, text, and sudden whole-sky changes are not — for weather, describe the first visible seconds (light dims, first drops hit the path) rather than a finished storm.
- Camera: steady first-person, slight handheld sway, no cuts, no zoom bursts. Keep lighting, colours and layout continuous with the CURRENT VIEW. Append the STYLE line verbatim.

Input kinds:
- action: the player does something -> rule and prepare both branches as above.
- declare: the player states a fact about the world in director mode ("there is an elephant on the road", "it starts to rain"). Accept it: kind=declare, ruling=allowed, verb=declare, and both branches make it true and VISIBLE in the next 4 seconds (the elephant walks into view). Record it as entities/facts. Only refuse (denied) if it contradicts a committed FACT.
  The video model cannot morph one object into another or rewrite the whole frame. If the declaration implies a transformation ("the car turns into a dinosaur"), stage it as an ARRIVAL or REVEAL instead: the dinosaur steps out from behind the car / walks in from the edge of the frame while the car stays, and say so in visible_result; keep the camera and scene unchanged.
- question: the player asks about the world -> kind=question, ruling=allowed; answer in narration (from FACTS and what is visible), no state change, clip_prompt may be a calm look-around.
If the input is marked PLOT EVENT, it is a world event (not a player action): kind=action, ruling=allowed, verb=event, and both branches describe the event happening clearly on camera (failure = a milder variant)."""


class GMAgent(Agent):
    name = "gm"

    def run(self, player_text: str, plot_event: bool = False, current_view: str = "") -> GMResult:
        st = self.session.state
        kind = "PLOT EVENT (world-driven)" if plot_event else "PLAYER SAYS"
        view = f"\n\nCURRENT VIEW (what is on screen right now; the video clip MUST start from exactly this and keep its lighting, colours and layout): {current_view}" if current_view else ""
        user = f"WORLD STATE:\n{st.summary_for_llm()}{view}\n\n{kind}: {player_text}"
        res = self.llm.json(SYSTEM.replace("{LANG}", settings.narration_lang), user, GMResult)
        for b in (res.success, res.failure):
            if st.scene.style and st.scene.style.lower() not in b.clip_prompt.lower():
                b.clip_prompt = b.clip_prompt.rstrip(". ") + ". " + st.scene.style
        self.emit("gm", text=player_text, plot_event=plot_event, result=res.model_dump())
        return res

    def roll(self, res: GMResult, n: int) -> tuple[bool, int | None]:
        """Deterministic per (session, n). d20 against a DC derived from difficulty."""
        if res.ruling == "allowed":
            return True, None
        if res.ruling == "denied":
            return False, None
        seed = zlib.crc32(f"{self.session.root.name}:{n}".encode())
        r = random.Random(seed).randint(1, 20)
        return r >= 2 * res.difficulty - 1, r

    @staticmethod
    def idle_prompt(scene_description: str, style: str) -> str:
        return (f"First-person POV, the viewer stands still. {scene_description} Camera static, no cuts, "
                f"only subtle ambient motion: foliage and fabric stir in a light breeze, dust or light flickers softly. {style}")
