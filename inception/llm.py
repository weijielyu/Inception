"""Thin provider-agnostic LLM layer.

Every agent talks to the model through `LLM.json(system, user, schema)`, which returns a
dict validated against a pydantic model. Two providers:
  * deepseek  — OpenAI-compatible endpoint, JSON mode
  * anthropic — official SDK, structured outputs via output_config.format
A separate `VLM` wrapper does image-conditioned JSON calls (for QC / scene captioning).
"""
from __future__ import annotations

import base64
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .config import settings

log = logging.getLogger("inception.llm")
T = TypeVar("T", bound=BaseModel)


def _strip_fences(text: str) -> str:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    return m.group(1).strip() if m else text


def _schema_block(model: Type[BaseModel]) -> str:
    return json.dumps(model.model_json_schema(), ensure_ascii=False)


class LLM:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.llm_provider
        if self.provider == "deepseek":
            from openai import OpenAI

            if not settings.deepseek_api_key:
                raise RuntimeError("DEEPSEEK_API_KEY (or DEEPSEEK_API_KEY_FILE) is not set")
            self.client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
            self.model = settings.deepseek_model
        elif self.provider == "anthropic":
            import anthropic

            self.client = anthropic.Anthropic()
            self.model = settings.anthropic_model
        else:
            raise ValueError(f"unknown LLM provider {self.provider}")

    # ------------------------------------------------------------------ public
    def json(self, system: str, user: str, schema: Type[T], retries: int = 2) -> T:
        """Call the model and parse/validate into `schema`. Retries on bad JSON."""
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            t0 = time.time()
            raw = self._call_json(system, user, schema)
            try:
                obj = schema.model_validate_json(_strip_fences(raw))
                log.debug("%s ok in %.1fs", schema.__name__, time.time() - t0)
                return obj
            except ValidationError as e:
                last_err = e
                log.warning("validation failed (attempt %d) for %s: %s", attempt, schema.__name__, str(e)[:300])
                user = user + f"\n\nYour previous answer failed validation: {str(e)[:500]}\nReturn ONLY valid JSON matching the schema."
        raise RuntimeError(f"LLM returned invalid {schema.__name__}: {last_err}")

    def text(self, system: str, user: str) -> str:
        if self.provider == "deepseek":
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.8,
            )
            return r.choices[0].message.content or ""
        r = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system,
            output_config={"effort": settings.anthropic_effort},
            messages=[{"role": "user", "content": user}],
        )
        return next((b.text for b in r.content if b.type == "text"), "")

    # ----------------------------------------------------------------- private
    def _call_json(self, system: str, user: str, schema: Type[BaseModel]) -> str:
        if self.provider == "deepseek":
            sys_prompt = system + "\n\nRespond with a single JSON object (no prose) matching this JSON schema:\n" + _schema_block(schema)
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            return r.choices[0].message.content or ""
        # anthropic: structured output guarantees schema-valid JSON in the first text block
        r = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system,
            output_config={
                "effort": settings.anthropic_effort,
                "format": {"type": "json_schema", "schema": _strict_schema(schema)},
            },
            messages=[{"role": "user", "content": user}],
        )
        return next((b.text for b in r.content if b.type == "text"), "")


def _strict_schema(model: Type[BaseModel]) -> dict[str, Any]:
    """Anthropic structured outputs want additionalProperties:false and all keys required."""
    s = model.model_json_schema()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                node["additionalProperties"] = False
                node["required"] = list(node["properties"].keys())
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(s)
    return s


# ----------------------------------------------------------------------------- vision
def _img_b64(path: str | Path) -> tuple[str, str]:
    p = Path(path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return base64.standard_b64encode(p.read_bytes()).decode(), mime


class VLM:
    """Image(s)+text -> JSON. Used by the QC agent and for captioning the seed image."""

    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.vlm_provider
        if self.provider == "openrouter":
            from openai import OpenAI

            if not settings.openrouter_api_key:
                raise RuntimeError("OPENROUTER_API_KEY (or OPENROUTER_API_KEY_FILE) is not set")
            self.client = OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url)
            self.model = settings.vlm_model
        elif self.provider == "anthropic":
            import anthropic

            self.client = anthropic.Anthropic()
            self.model = settings.anthropic_model
        elif self.provider == "none":
            self.client = None
        else:
            raise ValueError(f"unknown VLM provider {self.provider}")

    @property
    def available(self) -> bool:
        return self.client is not None

    def json(self, system: str, user: str, images: list[str | Path], schema: Type[T], retries: int = 1) -> T:
        if not self.available:
            raise RuntimeError("VLM disabled")
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            raw = self._call(system, user, images, schema)
            try:
                return schema.model_validate_json(_strip_fences(raw))
            except ValidationError as e:
                last_err = e
                log.warning("VLM validation failed (attempt %d) for %s: %s | raw: %s", attempt, schema.__name__, str(e)[:200], raw[:200])
                user = user + f"\n\nYour previous answer failed validation: {str(e)[:400]}\nReturn ONLY a JSON object with exactly the schema's top-level keys."
        raise RuntimeError(f"VLM returned invalid {schema.__name__}: {last_err}")

    def _call(self, system: str, user: str, images: list[str | Path], schema: Type[BaseModel]) -> str:
        if self.provider == "openrouter":
            content: list[dict] = []
            for img in images:
                b64, mime = _img_b64(img)
                content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
            content.append({"type": "text", "text": user})
            sys_prompt = system + "\n\nRespond with a single JSON object matching this schema:\n" + _schema_block(schema)
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": content}],
                temperature=0.2,
            )
            return r.choices[0].message.content or ""
        content = []
        for img in images:
            b64, mime = _img_b64(img)
            content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}})
        content.append({"type": "text", "text": user})
        r = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": _strict_schema(schema)}},
            messages=[{"role": "user", "content": content}],
        )
        return next((b.text for b in r.content if b.type == "text"), "")
