"""
llm.py — thin Claude wrapper used by every agent.

One model (Sonnet) for the whole system. Provides plain-text and JSON helpers,
and a `has_llm` flag so agents can degrade gracefully when no key is configured.
"""

import json
import re
from typing import Any

from app.core.config import settings

_client = None


def has_llm() -> bool:
    return settings.has_llm


def _get_client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def complete(system: str, user: str, max_tokens: int = 800,
             model: str | None = None) -> str:
    """Single-turn completion → text."""
    resp = _get_client().messages.create(
        model=model or settings.CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def complete_json(system: str, user: str, max_tokens: int = 800) -> Any:
    """Completion expected to return JSON; extracts the first JSON value found."""
    text = complete(system + "\nReturn ONLY valid JSON.", user, max_tokens)
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in model output: {text[:200]}")
    return json.loads(match.group(0))
