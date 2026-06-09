"""Builds the runtime prompt fed to the generator LLM.

Design: profile + question drive 90% of the answer.
Examples are collapsed to a vocabulary list that influences style only (10%).
"""
from __future__ import annotations

from app.prompts.runtime import RUNTIME_PROMPT

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
    seen = set()
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


def _build_vocab_block(examples: list[dict], profile: dict | None) -> str:
    """Extract unique reply-words + profile phrases → style-only vocabulary block."""
    phrases: list[str] = []

    # From profile common_phrases
    traits = (profile or {}).get("traits") or {}
    for cp in traits.get("common_phrases") or []:
        if cp and cp not in phrases:
            phrases.append(cp)
    for cp in traits.get("slang") or []:
        if cp and cp not in phrases:
            phrases.append(str(cp))

    # From real example replies (short ones only — long replies are content, not vocab)
    seen: set[str] = set(phrases)
    for e in examples:
        r = (e.get("reply") or "").strip()
        if r and len(r) <= 60 and r not in seen:
            seen.add(r)
            phrases.append(r)

    if not phrases:
        return "(אין ביטויים ייחודיים — השתמש בסגנון קליל וקצר)"
    return "  " + " / ".join(f'"{p}"' for p in phrases[:20])


def build_runtime_prompt(
    *,
    examples: list[dict],
    incoming_message: str,
    style_profile: dict | None = None,
) -> str:
    profile_text = _format_profile(style_profile)
    vocab_block = _build_vocab_block(examples, style_profile)
    return RUNTIME_PROMPT.format(
        profile=profile_text,
        vocab=vocab_block,
        incoming=incoming_message,
    )
