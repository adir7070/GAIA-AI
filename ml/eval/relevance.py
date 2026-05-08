"""LLM-judge relevance score: does the response actually address the incoming message?

1 = ignores or contradicts; 3 = partial; 5 = fully addresses.
"""
from __future__ import annotations

import asyncio
import re
import statistics

from ml._llm import chat

PROMPT = """Rate how well the response addresses the incoming message on a 1-5 scale.
1 = ignores or contradicts the question
3 = partially relevant
5 = fully addresses it

[INCOMING MESSAGE]
{incoming}

[RESPONSE]
{response}

Reply with a single digit 1-5.
"""


async def score_one(incoming: str, response: str) -> int:
    out = await chat(PROMPT.format(incoming=incoming, response=response), temperature=0.0, max_tokens=4)
    m = re.search(r"[1-5]", out)
    return int(m.group(0)) if m else 3


async def relevance_scores(samples: list[dict]) -> dict:
    """`samples`: list of {incoming, model}."""
    scores = await asyncio.gather(*[score_one(s["incoming"], s.get("model", "")) for s in samples])
    if not scores:
        return {"mean": 0.0, "std": 0.0, "n": 0}
    return {"mean": statistics.mean(scores), "std": statistics.pstdev(scores), "n": len(scores)}
