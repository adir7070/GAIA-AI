"""Unified LLM client. Supports Anthropic, OpenAI, and Groq.

Groq uses an OpenAI-compatible API — we just point the AsyncOpenAI client at
their base URL with the GROQ_API_KEY.
"""
from __future__ import annotations

import logging
from typing import Literal

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

log = logging.getLogger(__name__)

Provider = Literal["anthropic", "openai", "groq"]

_anthropic: AsyncAnthropic | None = None
_openai: AsyncOpenAI | None = None
_groq: AsyncOpenAI | None = None


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


def _get_groq() -> AsyncOpenAI:
    global _groq
    if _groq is None:
        _groq = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
        )
    return _groq


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

    # OpenAI and Groq share the same chat-completions interface
    cli = _get_groq() if p == "groq" else _get_openai()
    chosen_model = model or (settings.GROQ_MODEL if p == "groq" else settings.OPENAI_MODEL)
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = await cli.chat.completions.create(
        model=chosen_model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    return (resp.choices[0].message.content or "").strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def generate_with_history(
    *,
    system: str,
    history: list[dict],
    max_tokens: int = 400,
    temperature: float = 0.6,
    provider: Provider | None = None,
    model: str | None = None,
) -> str:
    """Generate a reply given a system message and full conversation history.

    `history` must be [{"role": "user"|"assistant", "content": str}].
    The last element must have role "user" (the incoming message to answer).
    """
    p = provider or settings.LLM_PROVIDER
    if p == "anthropic":
        cli = _get_anthropic()
        msg = await cli.messages.create(
            model=model or settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=history,
        )
        return "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
    cli = _get_groq() if p == "groq" else _get_openai()
    chosen_model = model or (settings.GROQ_MODEL if p == "groq" else settings.OPENAI_MODEL)
    messages: list[dict] = [{"role": "system", "content": system}] + history
    resp = await cli.chat.completions.create(
        model=chosen_model,
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
