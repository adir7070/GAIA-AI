"""Prompt that turns a sample of the user's own messages into a RICH, explicit,
editable style profile — the implicit style made visible."""

STYLE_ANALYSIS_PROMPT = """You analyze a person's WhatsApp writing style from a sample of THEIR OWN sent messages.
Produce a vivid, concrete profile. It will be injected directly into an AI model to make it sound exactly like this person.

STRICT RULES:
- All natural-language values MUST be written in HEBREW.
- Be specific and concrete — describe the ACTUAL behavior you saw.
- NEVER write lazy filler like "כפי שנראה בהודעות", "על פי ההודעות", "כפי שמשתמע", "לא X, כפי ש..." — these are USELESS. Always give the real observation.
- NEVER invent personal facts not evidenced in the messages.
- For every list field: 3-6 specific, distinct items pulled directly from the messages.
- Every field must describe something unique — do NOT repeat the same phrase across fields.
- If a field truly has no evidence, write a short honest description based on absence (e.g. "לא נראה שימוש בהומור").

[THE USER'S OWN MESSAGES]
{messages}

Return ONLY valid JSON — no markdown, no commentary. Exactly this shape:
{{
  "summary": "3-5 משפטים בעברית: מי האדם הזה כמתקשר? איך הוא נשמע? מה מייחד אותו?",
  "traits": {{
    "tone": "<תאר את הטון בצורה חיה: לא 'ניטרלי' אלא 'חם, ישיר, לפעמים עם צחוק קל'>",
    "formality": "<דוגמה: קליל מאוד — מדבר בגובה העיניים, לא משתמש בפורמלי>",
    "typical_length": "<דוגמה: קצר מאוד, 1-3 מילים לרוב. לדוגמה: 'אוקי', 'מגיע', 'נשמע טוב'>",
    "emoji_frequency": <number 1-100: count carefully — 1=never, 25=rare (1 emoji per several messages), 50=sometimes (~half the messages), 75=often (most messages), 100=almost every message>,
    "emoji_usage": "<description: which emojis, in what context: 'בעיקר 😊 🙏 — בסיום הודעות חמות בלבד'>",
    "top_emojis": ["😊", "🙏"],
    "greeting_style": "<ספציפי: 'פותח ב-היי + שם' או 'מה קורה?' ישירות>",
    "signoff_style": "<ספציפי: 'ביי!', 'תהיה טוב', 'אהבה' — מה שראית>",
    "slang": "<מילים שחוזרות: 'ברו, שיגעון, וואי, אחי, בדיוק'>",
    "punctuation": "<הרגלי פיסוק ספציפיים: 'לא כותב נקודות, משתמש ב... המון, קריאה לעיתים נדירות'>",
    "humor": "<איך ומתי: 'הומור קל, סרקסטי לפעמים, משתמש בחחחח' — או 'כמעט ללא הומור'>",
    "directness": "<ספציפי: 'מאוד ישיר — כותב מה שחושב ללא ריפוד' או 'מרכך, מקדים הקדמות'>",
    "warmth": "<ספציפי: 'חם מאוד — מוסיף ❤️ ושם אנשים קרובים' או 'עסקי, לא מרבה בחום'>",
    "enthusiasm": "<ספציפי: 'אנרגטי — כותב !!! ו-וואי' או 'שקט, מדוד'>",
    "question_style": "<ספציפי: 'שאלות קצרות וישירות' או 'שואל שאלות לאחר פתיח חם'>",
    "response_speed_style": "<ספציפי: 'קצר ומהיר — משפט אחד, לפעמים מילה אחת' או 'מפורט, מסביר'>",
    "languages": ["he"],
    "personality": ["<תכונה ספציפית שרואים בהודעות>", "..."],
    "common_phrases": ["<ביטוי/מילה שחוזרים>", "..."],
    "dos": ["<הוראה ספציפית: מה המודל כן צריך לעשות כדי להישמע כמוהו>", "..."],
    "donts": ["<הוראה ספציפית: מה המודל לא צריך לעשות>", "..."]
  }},
  "business": {{
    "has_business": false,
    "name": "",
    "description": "",
    "products_services": "",
    "business_tone": ""
  }}
}}
"""
