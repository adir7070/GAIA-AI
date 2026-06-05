"""Prompt that turns a sample of the user's own messages into a RICH, explicit,
editable style profile — the implicit style made visible."""

STYLE_ANALYSIS_PROMPT = """You analyze a person's WhatsApp writing style from a large sample of THEIR OWN sent messages.
Produce a detailed, friendly profile the product shows the user: "this is how the model understands you".

Rules:
- Write ALL natural-language values in HEBREW (the product UI is Hebrew).
- Be accurate to the evidence below — do NOT invent facts about their life.
- Describe HOW they communicate (style + character), grounded in the messages.
- For every list field give 3-6 concrete items drawn from the messages.

[SAMPLE OF THE USER'S OWN MESSAGES]
{messages}

Return ONLY valid JSON (no markdown, no commentary) in EXACTLY this shape:
{{
  "summary": "3-5 משפטים בעברית: מי האדם הזה כמתקשר, איך הוא נשמע ואיך הוא עונה",
  "traits": {{
    "tone": "<הטון הכללי>",
    "formality": "<מאוד קליל / קליל / ניטרלי / רשמי>",
    "typical_length": "<אורך תשובה אופייני, עם דוגמה>",
    "emoji_usage": "<עד כמה ואיך משתמש באימוג'י>",
    "top_emojis": ["😄", "🙏", "..."],
    "greeting_style": "<איך הוא פותח שיחה / מתחיל הודעה>",
    "signoff_style": "<איך הוא מסיים שיחה / חותם>",
    "slang": "<סלנג ומילים אופייניות>",
    "punctuation": "<הרגלי פיסוק (נקודות, סימני קריאה, רווחים)>",
    "humor": "<האם ואיך משתמש בהומור>",
    "directness": "<ישיר וענייני / רך ומרכך / מתחמק>",
    "warmth": "<מידת חום ואמפתיה>",
    "enthusiasm": "<מידת התלהבות/אנרגיה>",
    "question_style": "<איך הוא שואל שאלות>",
    "response_speed_style": "<קצר ומהיר / מפורט ושקול>",
    "languages": ["he"],
    "personality": ["<תכונת אופי בתקשורת>", "..."],
    "common_phrases": ["<ביטוי/מילה שחוזרים>", "..."],
    "dos": ["<מה המודל *כן* צריך לעשות כדי להישמע כמוהו>", "..."],
    "donts": ["<מה המודל *לא* צריך לעשות>", "..."]
  }},
  "business": {{
    "has_business": <true אם נראה מההודעות שיש לו עסק/עבודה עצמאית, אחרת false>,
    "name": "<שם העסק אם מוזכר, אחרת ריק>",
    "description": "<מה העסק עושה אם משתמע מההודעות, אחרת ריק>",
    "products_services": "<מוצרים/שירותים אם מוזכרים, אחרת ריק>",
    "business_tone": "<טון מול לקוחות אם משתמע, אחרת ריק>"
  }}
}}
"""
