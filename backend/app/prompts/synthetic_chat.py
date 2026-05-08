"""Prompts for generating synthetic conversation histories per persona."""

HISTORY_GENERATOR_PROMPT = """You are role-playing AS a specific WhatsApp user, generating a realistic message history.

PERSONA (private - do NOT mention or describe in the messages):
{persona_json}

LANGUAGE: {language}

Now generate {n_messages} natural WhatsApp messages this user would send.
Mix outgoing solo messages, replies to a few different (imagined) contacts, and brief multi-message bursts.
Cover varied topics drawn from the persona's interests.

Output strictly a JSON array of objects, no extra text:
[
  {{"text": "<message>", "context": "<short label like 'reply to friend about plans'>"}},
  ...
]

Style fidelity is critical - every message must read as if THIS person wrote it.
Do NOT describe the style. Just produce the messages.
"""


PAIR_GENERATOR_PROMPT = """You are role-playing AS the user defined by this persona.
You will receive an INCOMING message addressed to the user, plus their recent history.
Your job: write the EXACT response this user would send back, keeping their writing style intact.

PERSONA (private - never mention or quote):
{persona_json}

LANGUAGE: {language}

[USER'S HISTORY - sample messages by this user]
{history_sample}

[INCOMING MESSAGE FROM SOMEONE ELSE]
{incoming}

Output ONLY the response text the user would send. No labels. No quotes. No commentary.
"""


INCOMING_GENERATOR_PROMPT = """Generate {n} short, varied incoming WhatsApp messages someone might send to a person
matching this persona summary:

{persona_summary}

Mix message types: questions, plans, small talk, work updates, requests for help, scheduling, links shared.
Output a JSON array of strings, no extra text.
"""
