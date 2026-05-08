"""Unified LLM client. Supports Anthropic (default) and OpenAI."""
from __future__ import annotations

import logging
from typing import Literal

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

log = logging.getLogger(__name__)

Provider = Literal["anthropic", "openai"]

_anthropic: AsyncAnthropic | None = None
_openai: AsyncOpenAI | None = None


def _get_anthropic() -> AsyncAnthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic


def _get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def generate_text(
    prompt: str,
    *,
    system: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    provider: Provider | None = None,
    model: str | None = None,
) -> str:
    p = provider or settings.LLM_PROVIDER
    if p == "anthropic":
        cli = _get_anthropic()
        msg = await cli.messages.create(
            model=model or settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if hasattr(block, "text")).strip()

    cli = _get_openai()
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = await cli.chat.completions.create(
        model=model or settings.OPENAI_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    return (resp.choices[0].message.content or "").strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def judge_pair(
    history: str,
    incoming: str,
    response_a: str,
    response_b: str,
    *,
    provider: Provider | None = None,
) -> str:
    """Returns 'A' or 'B'."""
    from app.prompts.judge import JUDGE_PROMPT

    prompt = JUDGE_PROMPT.format(
        history=history, incoming=incoming, response_a=response_a, response_b=response_b
    )
    out = await generate_text(prompt, provider=provider, max_tokens=4, temperature=0.0)
    out = out.strip().upper()
    return "A" if out.startswith("A") else "B"
