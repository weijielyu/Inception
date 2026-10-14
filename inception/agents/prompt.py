"""Prompt agent: narrative beat -> shot spec for the video model (first-person, continuous
from the current frame). Also produces the list of things that must be visible, for QC."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .base import Agent
from .prediction import Outcome


class ShotSpec(BaseModel):
    prompt: str = Field(description="video prompt, <= 80 words, first-person POV, present tense, describes motion and what is revealed; ends with the style line")
    negative_prompt: str = Field(default="", description="short negative prompt")
    camera: str = Field(default="first-person handheld, eye level", description="camera behaviour")
    expected_visible: list[str] = Field(description="2-4 short checks a judge can verify in the frames, e.g. 'a hole in the ground', 'a wooden box'")


SYSTEM = """You are the PROMPT agent. Turn the outcome and narration of one turn into ONE image-to-video prompt. The video model starts from the CURRENT FRAME (the player's current first-person view) and must continue it seamlessly.

Rules:
- First-person POV, the camera is the player's eyes. Hands may appear if the action involves them.
- Describe visible motion over ~4 seconds: what the player does and what changes or is revealed. No dialogue, no text overlays, no cuts.
- Do not introduce anything that is not in the outcome / plot event. Keep the scene, lighting and style continuous with the current frame.
- Append the STYLE line verbatim at the end of the prompt."""


class PromptAgent(Agent):
    name = "prompt"

    def run(self, outcome: Outcome, narration: str, plot_event_visible: str) -> ShotSpec:
        st = self.session.state
        user = (
            f"SCENE: {st.scene.description}\nSTYLE: {st.scene.style}\n"
            f"OUTCOME: {outcome.visible_result}\nNARRATION: {narration}\nPLOT EVENT (visual): {plot_event_visible or 'none'}"
        )
        spec = self.llm.json(SYSTEM, user, ShotSpec)
        if st.scene.style and st.scene.style.lower() not in spec.prompt.lower():
            spec.prompt = spec.prompt.rstrip(". ") + ". " + st.scene.style
        self.emit("shot", spec=spec.model_dump())
        return spec
