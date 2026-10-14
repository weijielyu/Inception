from __future__ import annotations

import logging

from ..llm import LLM
from ..state import Session


class Agent:
    name = "agent"

    def __init__(self, llm: LLM, session: Session):
        self.llm = llm
        self.session = session
        self.log = logging.getLogger(f"inception.{self.name}")

    def emit(self, event: str, **payload) -> None:
        self.session.log(self.name, event, **payload)
