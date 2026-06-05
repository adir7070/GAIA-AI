"""Builds the runtime prompt fed to the generator LLM."""
from __future__ import annotations

from app.prompts.runtime import RUNTIME_PROMPT

# Emoji-related traits are intentionally NOT injected into the generator — they
# pushed the model to add emoji to every reply. Emoji frequency is learned from
# the real example pairs instead.
_SKIP_TRAITS = {"top_emojis", "emoji_usage"}


def _format_profile(profile: dict | None) -> str:
    if not profile:
        return ""
    parts: list[str] = []
    if profile.get("summary"):
        parts.append(profile["summary"])
    traits = profile.get("traits") or {}
    for k, v in traits.items():
        if not v or k in _SKIP_TRAITS:
            continue
        val = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
        parts.append(f"{k}: {val}")
    biz = profile.get("business") or {}
    if biz.get("name") or biz.get("description"):
        blines = [f"{k}: {v}" for k, v in biz.items() if v and k != "has_business"]
        if blines:
            parts.append("BUSINESS CONTEXT (reply consistently with this when relevant):")
            parts.extend(blines)
    return "\n".join(parts)


def build_runtime_prompt(
    *,
    examples: list[dict],
    incoming_message: str,
    style_profile: dict | None = None,
) -> str:
    ex_block = (
        "\n---\n".join(
            f"Them: {e.get('incoming','')}\nYou: {e.get('reply','')}" for e in examples if e.get("reply")
        )
        or "(no examples yet)"
    )
    profile_text = _format_profile(style_profile) or "(none)"
    return RUNTIME_PROMPT.format(
        examples=ex_block,
        profile=profile_text,
        incoming=incoming_message,
    )
