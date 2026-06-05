"""Builds the runtime prompt fed to the generator LLM."""
from __future__ import annotations

from app.prompts.runtime import RUNTIME_PROMPT


def _format_profile(profile: dict | None) -> str:
    if not profile:
        return ""
    parts: list[str] = []
    if profile.get("summary"):
        parts.append(profile["summary"])
    traits = profile.get("traits") or {}
    for k, v in traits.items():
        if not v:
            continue
        val = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
        parts.append(f"{k}: {val}")
    return "\n".join(parts)


def build_runtime_prompt(
    *,
    similar_history: list[str],
    recent_turns: list[dict],
    incoming_message: str,
    style_profile: dict | None = None,
) -> str:
    history_block = "\n".join(f"- {t}" for t in similar_history if t)
    turns_block = "\n".join(
        f"[{t.get('direction','?').upper()}] {t.get('text','')}" for t in recent_turns
    )
    base = RUNTIME_PROMPT.format(
        history=history_block or "(none)",
        recent=turns_block or "(none)",
        incoming=incoming_message,
    )
    profile_text = _format_profile(style_profile)
    if profile_text:
        # The user-editable profile is authoritative — honor it alongside the examples.
        base = (
            "[USER STYLE PROFILE — how this user communicates; honor this]\n"
            f"{profile_text}\n\n" + base
        )
    return base
