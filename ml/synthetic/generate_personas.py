"""Generate N synthetic users with hidden writing styles.

Output: data/synthetic/personas.jsonl (one persona per line)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

# allow `python -m synthetic.generate_personas` from ml/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from ml._llm import chat, gather_with_concurrency  # noqa: E402
from ml.synthetic._diversity import sample_seed  # noqa: E402

PROMPT = """You are a creative writer building a believable WhatsApp user persona.

Persona seed (the persona must adhere to these style traits, but DO NOT mention or describe
the style anywhere in the output):
{seed_json}

Output strictly valid JSON with this shape:
{{
  "user_id": "{user_id}",
  "language": "{language}",
  "persona_summary": "<2-3 sentences describing the person, NOT the style>",
  "topics": ["work","friends","study","hobby","family"]
}}

No text outside the JSON.
"""

OUT = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "personas.jsonl"


async def make_one(seed: dict) -> dict:
    prompt = PROMPT.format(
        seed_json=json.dumps(seed, ensure_ascii=False, indent=2),
        user_id=seed["user_id"],
        language=seed["language"],
    )
    text = await chat(prompt, temperature=0.95, max_tokens=600)
    text = _extract_json(text)
    parsed = json.loads(text)
    parsed["hidden_style"] = seed
    return parsed


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--concurrency", type=int, default=4)
    args = p.parse_args()

    rng = random.Random(args.seed)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    seeds = [sample_seed(rng, user_id=f"u_{i:04d}") for i in range(args.n)]

    print(f"Generating {args.n} personas with concurrency={args.concurrency}…")
    coros = [make_one(s) for s in seeds]
    results = await gather_with_concurrency(coros, args.concurrency)

    with OUT.open("w", encoding="utf-8") as f:
        for p in results:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"Wrote {len(results)} personas → {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
