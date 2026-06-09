"""Builds the runtime prompt fed to the generator LLM.

Design:
  • Profile   → dominant (who this person is)
  • Examples  → top-3 closest semantic pairs, shown as style reference only (~5%)
  • Incoming  → non-negotiable — the model must answer exactly what was asked
"""
from __future__ import annotations

from app.prompts.runtime import RUNTIME_PROMPT, SYSTEM_PROMPT

_SKIP_TRAITS = {"top_emojis", "emoji_usage"}

_TRAIT_LABELS: dict[str, str] = {
    "tone": "טון כללי",
    "formality": "רמת רשמיות",
    "typical_length": "אורך תשובה אופייני",
    "greeting_style": "פתיחת שיחה",
    "signoff_style": "סיום שיחה",
    "slang": "סלנג ומילים אופייניות",
    "punctuation": "פיסוק",
    "humor": "הומור",
    "directness": "ישירות",
    "warmth": "חום ואמפתיה",
    "enthusiasm": "אנרגיה",
    "question_style": "סגנון שאלות",
    "response_speed_style": "קצב תגובה",
    "languages": "שפות",
    "personality": "אישיות בתקשורת",
    "common_phrases": "ביטויים שחוזרים",
    "dos": "מה כן לעשות",
    "donts": "מה לא לעשות",
}


def _format_profile(profile: dict | None) -> str:
    if not profile:
        return "אין פרופיל — ענה בצורה קלילה, קצרה וישירה."
    parts: list[str] = []
    if profile.get("summary"):
        parts.append(f"סיכום: {profile['summary']}")
    traits = profile.get("traits") or {}
    priority = [
        "tone", "formality", "typical_length", "warmth", "directness",
        "humor", "slang", "greeting_style", "personality", "dos", "donts",
        "common_phrases", "enthusiasm", "punctuation",
    ]
    seen: set[str] = set()
    for k in priority + [k for k in traits if k not in priority]:
        if k in seen or k in _SKIP_TRAITS:
            continue
        seen.add(k)
        v = traits.get(k)
        if not v:
            continue
        label = _TRAIT_LABELS.get(k, k)
        val = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
        parts.append(f"• {label}: {val}")
    biz = profile.get("business") or {}
    if biz.get("name") or biz.get("description"):
        parts.append("── עסק ──")
        for k, v in biz.items():
            if v and k not in {"has_business"}:
                parts.append(f"  {k}: {v}")
    return "\n".join(parts)


def _format_examples(examples: list[dict]) -> str:
    """Format top-3 closest pairs as style-reference conversation snippets.

    These are real (their message → your reply) pairs retrieved by semantic
    similarity. They show HOW the person writes, not what to say.
    Capped at 3 to keep their influence minimal.
    """
    if not examples:
        return "(אין דוגמאות — הסגנון מגיע מהאיפיון בלבד)"

    lines: list[str] = []
    for e in examples[:3]:
        incoming = (e.get("incoming") or "").strip()[:120]
        reply = (e.get("reply") or "").strip()[:120]
        if incoming and reply:
            lines.append(f"הם: {incoming}\nאני: {reply}")

    if not lines:
        return "(אין דוגמאות — הסגנון מגיע מהאיפיון בלבד)"
    return "\n\n".join(lines)


def build_runtime_prompt(
    *,
    examples: list[dict],
    incoming_message: str,
    style_profile: dict | None = None,
) -> str:
    profile_text = _format_profile(style_profile)
    examples_text = _format_examples(examples)
    return RUNTIME_PROMPT.format(
        profile=profile_text,
        examples=examples_text,
        incoming=incoming_message,
    )


def build_system_message(style_profile: dict | None = None) -> str:
    """System message for multi-turn playground chat.

    Profile only — no examples. Incoming message is supplied separately
    as the final user turn in the conversation history array.
    """
    return SYSTEM_PROMPT.format(profile=_format_profile(style_profile))
