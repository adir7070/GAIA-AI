"""Baseline response generators used by run_all.py."""
from __future__ import annotations

import os

from ml._llm import chat

ZERO_SHOT_PROMPT = """A user has written the following messages in the past:
{history}

A new message has just arrived:
{incoming}

Write the response this user would write. Match their style as best you can. Reply only with the response text."""


FEW_SHOT_PROMPT = """You will see {k} example messages from a specific WhatsApp user. They reflect this user's writing style.
Then you'll see a new incoming message addressed to them.

Examples (the user's own messages):
{history}

Incoming message:
{incoming}

Now write the response THIS user would write — matching their length, punctuation, emoji habits, slang, and rhythm.
Reply only with the response text."""


async def zero_shot(history: list[str], incoming: str) -> str:
    h = "\n".join(f"- {m}" for m in history) or "(no history)"
    p = ZERO_SHOT_PROMPT.format(history=h, incoming=incoming)
    return (await chat(p, temperature=0.7, max_tokens=300)).strip().strip('"')


async def few_shot(history: list[str], incoming: str, k: int = 5) -> str:
    sample = history[:k]
    h = "\n".join(f"- {m}" for m in sample)
    p = FEW_SHOT_PROMPT.format(k=len(sample), history=h, incoming=incoming)
    return (await chat(p, temperature=0.7, max_tokens=300)).strip().strip('"')


async def fine_tuned(history: list[str], incoming: str, adapter: str | None = None) -> str:
    """Stub. If GAIA_LORA_ADAPTER is set + transformers installed, route there.
    Otherwise we fallback to few-shot so the eval pipeline still runs end-to-end.
    """
    adapter = adapter or os.getenv("GAIA_LORA_ADAPTER")
    if not adapter:
        return await few_shot(history, incoming, k=8)
    # Lazy import - only if user actually has a checkpoint
    from ml.inference._loaded import generate_from_adapter

    return await generate_from_adapter(adapter, history, incoming)
