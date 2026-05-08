"""Prompts for generating synthetic users with hidden writing styles.

Spec reference: §10. Per the design we DO NOT leak the explicit style description
into the training data - the LLM-generator uses the hidden style internally to
keep the persona consistent, but the final dataset only stores conversations.
"""

PERSONA_GENERATOR_PROMPT = """You are a creative writer building a believable WhatsApp user persona.

Persona seed: {seed}

Constraints (must be internally consistent across all 50+ messages this persona will produce):
- Demographics & life context (age range, occupation, social circle): pick something plausible matching the seed.
- Writing style: pick a CONSISTENT style profile, including:
    * average message length (very short / short / medium / long)
    * punctuation tendencies
    * emoji usage frequency
    * slang use (heavy / moderate / none)
    * formality level
    * greeting habits and signoffs
    * rhythm (single-burst vs. multi-message replies)
- Topics they care about (work, friends, study, hobbies).

Output strictly valid JSON with the following shape:
{{
  "user_id": "{user_id}",
  "language": "he" | "en",
  "persona_summary": "<2-3 sentences describing the person, NOT the style>",
  "hidden_style": {{
     "avg_length": "short|medium|long",
     "punctuation": "<short description>",
     "emoji": "none|sparse|frequent|heavy",
     "slang": "none|some|heavy",
     "formality": "very_casual|casual|neutral|formal",
     "greeting_habits": "<short description>",
     "rhythm": "single|multi|mixed"
  }},
  "topics": ["work","friends","study","hobby","family"]
}}

Do not add any text outside the JSON.
"""
