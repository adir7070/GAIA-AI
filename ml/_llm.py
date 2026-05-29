"""Shared LLM wrapper for ml/. Supports Anthropic, OpenAI, and Groq.

Configured via env (LLM_PROVIDER + the relevant API key).
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Literal

from anthropic import AsyncAnthropic
from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Load the repo-root .env regardless of the cwd the script is launched from
# (ml/ scripts are run via `cd ml && python -m ...`, so the .env is one level up).
load_dotenv(find_dotenv(usecwd=True))

Provider = Literal["anthropic", "openai", "groq"]

PROVIDER: Provider = os.getenv("LLM_PROVIDER", "groq")  # type: ignore
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

_anthropic: AsyncAnthropic | None = None
_openai: AsyncOpenAI | None = None
_groq: AsyncOpenAI | None = None


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


def _gclient() -> AsyncOpenAI:
    global _groq
    if _groq is None:
        _groq = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY", ""),
            base_url=GROQ_BASE_URL,
        )
    return _groq


# Deterministic global rate limiter: free Groq tiers cap requests-per-minute
# (~30 RPM). Pacing the START of every request to a minimum interval keeps us
# under the ceiling so we (almost) never trigger a 429 in the first place —
# far more reliable than relying on retry/backoff, which becomes a retry storm.
# Set LLM_MIN_INTERVAL_S (e.g. 2.2 → ~27 RPM) to enable.
_MIN_INTERVAL = float(os.getenv("LLM_MIN_INTERVAL_S", "0"))
_rate_lock = asyncio.Lock()
_last_call_t = 0.0


async def _throttle() -> None:
    if _MIN_INTERVAL <= 0:
        return
    global _last_call_t
    async with _rate_lock:
        wait = _MIN_INTERVAL - (time.monotonic() - _last_call_t)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_t = time.monotonic()


# Jittered backoff as a SECOND line of defense if a 429 still slips through.
@retry(stop=stop_after_attempt(12), wait=wait_random_exponential(multiplier=2, max=60))
async def chat(
    prompt: str,
    *,
    system: str | None = None,
    temperature: float = 0.8,
    max_tokens: int = 1500,
    provider: Provider | None = None,
    model: str | None = None,
) -> str:
    await _throttle()
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

    cli = _gclient() if p == "groq" else _oclient()
    chosen = model or (GROQ_MODEL if p == "groq" else OPENAI_MODEL)
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    r = await cli.chat.completions.create(
        model=chosen,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=msgs,
    )
    return (r.choices[0].message.content or "").strip()


def extract_json(text: str) -> str:
    """Extract the first complete JSON array/object from an LLM response.

    Strips ``` fences and any prose before/after the JSON, and stops at the
    matching closing bracket — this tolerates the trailing junk that smaller
    models often append (the "Extra data" JSONDecodeError).
    """
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if "\n" in t:
            t = t.split("\n", 1)[1]
    start = next((i for i, c in enumerate(t) if c in "[{"), None)
    if start is None:
        return t.strip()
    open_ch = t[start]
    close_ch = "]" if open_ch == "[" else "}"
    depth = 0
    in_str = esc = False
    for j in range(start, len(t)):
        c = t[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return t[start : j + 1]
    return t[start:].strip()


async def gather_with_concurrency(coros, n: int):
    sem = asyncio.Semaphore(n)

    async def _wrap(c):
        async with sem:
            return await c

    return await asyncio.gather(*(_wrap(c) for c in coros))
