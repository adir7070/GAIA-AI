# Gaia AI - Course Project Proposal

## English (one-page form for submission)

### Title
**Gaia AI: Personalized Response Generation via Implicit User Style Learning**

### Motivation
In communication-heavy roles (educators, consultants, service professionals),
users are flooded with messages whose answers follow a consistent personal
style. This project explores whether large language models can learn and
reproduce a user's communication style from historical chat data and generate
contextually appropriate responses in that style.

### Problem definition
Given a user's chat history and a new incoming message, the system generates a
response that (1) addresses the message content and (2) preserves the implicit
writing style of the user. Formulated as conditional text generation with
implicit style conditioning.

### Dataset (hybrid)

1. **Synthetic (primary).** 1,000 synthetic users, each with a consistent
   latent communication style (sampled from a diversity matrix; *not*
   leaked into the training data). Generated via Claude/GPT role-play.
   ~50,000 (history, incoming, target) triples.
2. **Real (evaluation only).** Opt-in, anonymized WhatsApp histories from a
   small number of consenting users, used for generalization tests only.

### Methodology
Fine-tune `Llama-3-8B-Instruct` with QLoRA (r=16, α=32, target=q/k/v/o,
4-bit nf4 quant). Input: chat history + incoming message. Output: user-style
response.

### Baselines
- Zero-shot prompting (style instruction only).
- Few-shot prompting (5-8 examples from history).
- Fine-tuned model (proposed).

### Evaluation
**Style Indistinguishability Test (per lecturer feedback):** an LLM judge sees
history + incoming + two responses (oracle vs. our model), randomized order,
and must pick the user's. Accuracy ≈ 50% means our model is indistinguishable
from the oracle. Generator and judge use *different* providers to avoid bias.

Secondary: BGE-large embedding cosine similarity to user history, and an LLM
1-5 relevance score.

### Expected contribution
A study of whether large-scale synthetic user modeling generalizes to real
personalized response generation, framed around a strong indistinguishability
metric rather than a brittle "similarity score".

---

## עברית (גרסה לסקירה פנימית)

### כותרת
**Gaia AI: יצירת תשובות מותאמות אישית באמצעות למידת סגנון משתמש סמוי**

### מוטיבציה
בעידן של תקשורת אינטנסיבית (מרצים, יועצים, אנשי שירות), קיים עומס גבוה של
הודעות חוזרות הדורשות מענה דומה. לכל אדם יש סגנון כתיבה אישי עקבי שקשה לשחזר
ידנית. הפרויקט בוחן האם מודלי שפה גדולים יכולים ללמוד את הסגנון הזה מתוך
היסטוריית שיחות ולייצר תשובות חדשות בסגנון של המשתמש.

### הגדרת הבעיה
בהינתן היסטוריית שיחות של משתמש והודעה חדשה, המערכת נדרשת ליצור תשובה אשר:
1. עונה נכון על ההודעה.
2. משמרת את סגנון הכתיבה הייחודי של המשתמש.

הבעיה מוגדרת כמשימת יצירת טקסט מותנה עם למידת סגנון סמוי
(implicit style conditioning).

### דאטה (היברידי)

1. **דאטה סינתטי (עיקרי).** ~1,000 משתמשים סינתטיים, כל אחד עם סגנון כתיבה
   עקבי (מדגימים סגנונות שונים ממטריצת גיוון; הסגנון *אינו* דולף לדאטה
   האימון). נוצר באמצעות Claude/GPT. ~50,000 דוגמאות אימון.
2. **דאטה אמיתי (להערכה בלבד).** עם הסכמה מלאה, היסטוריות אנונימיות, רק
   לבדיקת הכללה.

### מתודולוגיה
Fine-tuning של `Llama-3-8B-Instruct` ב-QLoRA. קלט: היסטוריה + הודעה. פלט:
תשובה בסגנון המשתמש.

### Baselines
Zero-shot, Few-shot, וכמודל מוצע: הגרסה המאומנת.

### הערכה
**מבחן Indistinguishability** (בעקבות פידבק המרצה): שופט LLM רואה היסטוריה,
הודעה, ושתי תשובות (oracle והמודל שלנו), בסדר אקראי, וצריך לבחור את התשובה של
המשתמש. דיוק ~50% משמעו שהמודל בלתי ניתן להבחנה. המודל המייצר והשופט באים
מספקים שונים כדי לצמצם הטיה.

### תרומה צפויה
מחקר שבוחן האם דאטה סינתטי בקנה מידה גדול מאפשר למידת סגנון אישי שמכלילה
לדאטה אמיתי, עם מדידה חזקה (Indistinguishability) במקום מדד דמיון "רך".
