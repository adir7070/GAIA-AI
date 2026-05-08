"""Builds the runtime prompt fed to the generator LLM."""
from __future__ import annotations

from app.prompts.runtime import RUNTIME_PROMPT


def build_runtime_prompt(
    *,
    similar_history: list[str],
    recent_turns: list[dict],
    incoming_message: str,
) -> str:
    history_block = "\n".join(f"- {t}" for t in similar_history if t)
    turns_block = "\n".join(
        f"[{t.get('direction','?').upper()}] {t.get('text','')}" for t in recent_turns
    )
    return RUNTIME_PROMPT.format(
        history=history_block or "(none)",
        recent=turns_block or "(none)",
        incoming=incoming_message,
    )
