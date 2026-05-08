"""Build train/val/test jsonl from pairs.jsonl with the Llama-3 instruction format.

Output:
  data/synthetic/train.jsonl
  data/synthetic/val.jsonl
  data/synthetic/test.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

PAIRS = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "pairs.jsonl"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "synthetic"

SYSTEM = (
    "You mimic a specific user's WhatsApp writing style. "
    "Reply ONLY with the response text — match the user's length, punctuation, "
    "emoji habits, slang, and rhythm as inferred from the example messages."
)


def build_prompt(history: list[str], incoming: str) -> str:
    h = "\n".join(f"- {m}" for m in history) or "(none)"
    return f"""[STYLE HISTORY]
{h}

[NEW INCOMING MESSAGE]
{incoming}

[TASK]
Write the response THIS user would write, matching their style. Reply only with the response text.
"""


def to_chatml(row: dict) -> dict:
    """Output the Llama-3 chat-template-friendly fields used by SFTTrainer."""
    return {
        "user_id": row["user_id"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_prompt(row["history"], row["incoming_message"])},
            {"role": "assistant", "content": row["target_response"]},
        ],
    }


def split_by_user(rows: list[dict], rng: random.Random):
    """Group by user, then assign whole users to splits to avoid leakage."""
    by_user: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_user[r["user_id"]].append(r)
    users = list(by_user.keys())
    rng.shuffle(users)
    n = len(users)
    n_test = max(1, n // 10)
    n_val = max(1, n // 10)
    test_users = set(users[:n_test])
    val_users = set(users[n_test : n_test + n_val])
    train, val, test = [], [], []
    for u, rs in by_user.items():
        bucket = test if u in test_users else val if u in val_users else train
        bucket.extend(rs)
    return train, val, test


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rows = [json.loads(l) for l in PAIRS.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Loaded {len(rows)} pairs")

    rng = random.Random(args.seed)
    train, val, test = split_by_user(rows, rng)

    for name, data in (("train", train), ("val", val), ("test", test)):
        path = OUT_DIR / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(to_chatml(r), ensure_ascii=False) + "\n")
        # Also keep the raw triples for evaluation
        raw_path = OUT_DIR / f"{name}_raw.jsonl"
        with raw_path.open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {name}: {len(data)} rows → {path}")


if __name__ == "__main__":
    main()
