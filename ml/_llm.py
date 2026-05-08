"""Shared LLM wrapper for ml/. Supports Anthropic + OpenAI; configured via env."""
from __future__ import annotations

import asyncio
import os
from typing import Literal

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

Provider = Literal["anthropic", "openai"]

PROVIDER: Provider = os.getenv("LLM_PROVIDER", "anthropic")  # type: ignore
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

_anthropic: AsyncAnthropic | None = None
_openai: AsyncOpenAI | None = None


def _aclient() -> AsyncAnthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    return _anthropic


def _oclient() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _openai


@retry(stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=15))
async def chat(
    prompt: str,
    *,
    system: str | None = None,
    temperature: float = 0.8,
    max_tokens: int = 1500,
    provider: Provider | None = None,
    model: str | None = None,
) -> str:
    p: Provider = provider or PROVIDER
    if p == "anthropic":
        msg = await _aclient().messages.create(
            model=model or ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    r = await _oclient().chat.completions.create(
        model=model or OPENAI_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=msgs,
    )
    return (r.choices[0].message.content or "").strip()


async def gather_with_concurrency(coros, n: int):
    sem = asyncio.Semaphore(n)

    async def _wrap(c):
        async with sem:
            return await c

    return await asyncio.gather(*(_wrap(c) for c in coros))
