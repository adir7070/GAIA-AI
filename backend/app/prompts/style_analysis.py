"""Prompt that turns a sample of the user's own messages into an explicit,
human-readable style profile — the implicit style made visible and editable."""

STYLE_ANALYSIS_PROMPT = """You analyze a person's WhatsApp writing style from a sample of THEIR OWN sent messages.
Produce a concise, friendly profile the product shows the user: "this is how the model understands you".

Rules:
- Write all natural-language text in HEBREW (the product UI is Hebrew).
- Be accurate to the evidence below — do NOT invent facts about their life.
- Describe HOW they write and their communication character, not what they talked about.

[SAMPLE OF THE USER'S OWN MESSAGES]
{messages}

Return ONLY valid JSON (no markdown, no commentary) in exactly this shape:
{{
  "summary": "2-4 משפטים בעברית: מי האדם הזה כמתקשר ואיך הוא עונה",
  "traits": {{
    "tone": "<הטון הכללי>",
    "formality": "<מאוד קליל / קליל / ניטרלי / רשמי>",
    "typical_length": "<אורך תשובה אופייני>",
    "emoji_usage": "<עד כמה משתמש באימוג'י ואילו>",
    "slang": "<סלנג ושפה אופיינית>",
    "languages": ["he"],
    "punctuation": "<הרגלי פיסוק>",
    "personality": ["<תכונת אופי בתקשורת>", "<עוד תכונה>"],
    "common_phrases": ["<ביטוי/מילה שחוזרים אצלו>", "<עוד>"]
  }}
}}
"""
