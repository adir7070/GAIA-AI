"""For each persona, generate ~50 outgoing WhatsApp messages reflecting their hidden style.

Output: data/synthetic/histories.jsonl  (one row per persona with message list)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, for `from ml.* import`
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from ml._llm import chat, extract_json as _extract_json, gather_with_concurrency  # noqa: E402

PROMPT = """You are role-playing AS a specific WhatsApp user. Generate {n} natural WhatsApp messages this user would SEND to others.

Persona (private — never mention or describe in messages):
{persona_json}

Mix outgoing solo messages, replies to friends/colleagues/family, and brief multi-message bursts. Cover varied topics from the persona's interests.

CRITICAL: every message must read as if THIS specific person wrote it (style cues from their seed must show through naturally — length, punctuation, emoji habits, slang, formality, rhythm, greetings).

Output strictly a JSON array of strings, no extra text. Example:
["...", "..."]
"""

PERSONAS = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "personas.jsonl"
OUT = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "histories.jsonl"


async def gen_for(persona: dict, n: int) -> dict | None:
    prompt = PROMPT.format(
        n=n,
        persona_json=json.dumps(persona, ensure_ascii=False, indent=2),
    )
    try:
        text = await chat(prompt, temperature=0.95, max_tokens=1200)
        msgs = json.loads(_extract_json(text), strict=False)
        msgs = [str(m) for m in msgs if str(m).strip()]
    except Exception as e:  # noqa: BLE001 - skip a bad generation instead of killing the whole batch
        print(f"  skip history for {persona.get('user_id')}: {type(e).__name__}: {e}")
        return None
    if not msgs:
        return None
    return {"user_id": persona["user_id"], "messages": msgs}


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n-messages", type=int, default=50)
    p.add_argument("--concurrency", type=int, default=4)
    args = p.parse_args()

    if not PERSONAS.exists():
        raise SystemExit("personas.jsonl not found - run generate_personas.py first")

    personas = [json.loads(line) for line in PERSONAS.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Generating histories for {len(personas)} personas…")

    coros = [gen_for(p, args.n_messages) for p in personas]
    results = [r for r in await gather_with_concurrency(coros, args.concurrency) if r]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(results)}/{len(personas)} histories → {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
