"""Builds the runtime prompt fed to the generator LLM.

Design:
  • Profile   → dominant (who this person is)
  • Examples  → top-2 closest semantic pairs, style reference only (~30%)
  • Incoming  → non-negotiable — the model must answer exactly what was asked
"""
from __future__ import annotations
import re

from app.prompts.runtime import RUNTIME_PROMPT, SYSTEM_PROMPT

# Hebrew function/question words stripped before semantic search so that
# "מה אתה הכי אוהב לאכול?" → "אוהב לאכול" instead of matching "אהבה" sentences.
_HE_STOP = {
    "מה","מי","איך","כמה","מתי","איפה","למה","אם","כי","אבל","גם","כן","לא",
    "רק","כבר","עוד","כל","של","על","עם","אל","אני","אתה","את","הוא","היא",
    "אנחנו","הם","הן","אתם","אתן","הכי","ממש","קצת","מאוד","מאד","בדיוק",
    "פשוט","שלי","שלך","שלו","שלה","שלנו","שלהם","שלהן","יש","אין","בא",
    "לי","לך","לו","לה","לנו","להם","היה","הייתה","היו","הייתי","זה","זאת",
    "זו","אלה","אלו","כאן","שם","עכשיו","היום","מחר","אתמול","טוב","בסדר",
}


def extract_search_keywords(text: str) -> str:
    """Strip Hebrew function/question words → leave content words for vector search."""
    words = re.findall(r'[א-ת]+', text)
    content = [w for w in words if w not in _HE_STOP and len(w) > 1]
    return " ".join(content) if content else text

_SKIP_TRAITS = {"top_emojis", "emoji_usage", "emoji_frequency"}

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


def _emoji_instruction(freq: int, top_emojis: list | None, usage_desc: str | None) -> str:
    """Convert emoji_frequency scale (1-100) to an explicit model instruction."""
    freq = max(1, min(100, int(freq)))
    bar = "█" * (freq // 10) + "░" * (10 - freq // 10)
    if freq <= 15:
        rule = "כמעט אף פעם אל תשתמש באימוג'ים — רק במקרים נדירים מאוד"
    elif freq <= 35:
        rule = "השתמש באימוג'י לעיתים נדירות — אחד לכל כמה הודעות, לא בכל הודעה"
    elif freq <= 55:
        rule = "השתמש באימוג'י מדי פעם — בערך בכל שלישית מהתשובות"
    elif freq <= 75:
        rule = "השתמש באימוג'י לעיתים קרובות — ברוב ההודעות, אך לא בכולן"
    else:
        rule = "השתמש באימוג'י כמעט בכל הודעה — זה חלק מזהות הכתיבה"

    emojis_str = ""
    if top_emojis:
        emojis_str = f" אימוג'ים אופייניים: {' '.join(str(e) for e in top_emojis[:5])}"
    if usage_desc:
        emojis_str += f" ({usage_desc})"

    return f"• אימוג'ים [{bar} {freq}/100]: {rule}.{emojis_str}"


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
    """Format retrieved pairs as real conversation snippets.

    These are real (their message → your reply) pairs retrieved by semantic
    similarity. They carry both factual info AND style signal.
    Send all retrieved (up to 6) so facts are never silently dropped.
    """
    if not examples:
        return "(אין דוגמאות — הסגנון מגיע מהאיפיון בלבד)"

    lines: list[str] = []
    for e in examples[:6]:
        incoming = (e.get("incoming") or "").strip()[:150]
        reply = (e.get("reply") or "").strip()[:150]
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


def get_emoji_rule(profile: dict | None) -> str:
    """Standalone emoji rule string for the dedicated prompt section."""
    traits = (profile or {}).get("traits") or {}
    freq = traits.get("emoji_frequency")
    if freq is None:
        desc = traits.get("emoji_usage") or ""
        return f"השתמש באימוג'ים בצורה מתונה בהתאם לסגנון שבפרופיל.{' ' + desc if desc else ''}"
    return _emoji_instruction(freq, traits.get("top_emojis"), traits.get("emoji_usage"))


def _format_manual_facts(manual_pairs: list[dict]) -> str:
    """Format manually-taught Q→A pairs as explicit facts."""
    if not manual_pairs:
        return "(אין עובדות שנלמדו עדיין — השתמש בפרופיל ובשיחות)"
    lines = []
    for p in manual_pairs:
        q = (p.get("incoming") or "").strip()[:150]
        a = (p.get("reply") or "").strip()[:150]
        if q and a:
            lines.append(f"ש: {q}\nת: {a}")
    return "\n\n".join(lines) if lines else "(אין עובדות שנלמדו עדיין)"


def build_system_message(
    *,
    examples: list[dict],
    style_profile: dict | None = None,
    manual_pairs: list[dict] | None = None,
) -> str:
    """System message for multi-turn playground chat.

    Profile = primary identity, manual_pairs = explicit taught facts (always included),
    examples = semantic style calibration.
    """
    return SYSTEM_PROMPT.format(
        profile=_format_profile(style_profile),
        manual_facts=_format_manual_facts(manual_pairs or []),
        examples=_format_examples(examples),
        emoji_rule=get_emoji_rule(style_profile),
    )
