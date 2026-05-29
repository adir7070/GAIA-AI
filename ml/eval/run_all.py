"""Run the full evaluation pipeline across all baselines.

For each candidate model (zero-shot, few-shot, fine-tuned):
  - Style Indistinguishability vs. oracle (headline metric)
  - Style Similarity (embedding cosine vs. user history)
  - Relevance (LLM judge 1-5)

Reads test set from data/synthetic/test_raw.jsonl (produced by dataset/build_jsonl.py).
Writes results to ./results/eval_report.json + .md
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.eval._baselines import few_shot, fine_tuned, zero_shot  # noqa: E402
from ml.eval.indistinguishability import accuracy, run as run_indist, wilson_ci  # noqa: E402
from ml.eval.relevance import relevance_scores  # noqa: E402
from ml.eval.style_similarity import style_similarity_scores  # noqa: E402

TEST = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "test_raw.jsonl"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

BASELINES = {
    "zero_shot": zero_shot,
    "few_shot": few_shot,
    "fine_tuned": fine_tuned,
}


async def evaluate_one(name: str, fn, test: list[dict], limit: int | None) -> dict:
    rows = test[: limit or len(test)]
    print(f"\n=== {name} | {len(rows)} samples ===")
    samples = []
    for r in rows:
        out = await fn(r["history"], r["incoming_message"])
        samples.append(
            {
                "user_id": r["user_id"],
                "history": r["history"],
                "incoming": r["incoming_message"],
                "oracle": r["target_response"],
                "model": out,
            }
        )

    print(f"  → indistinguishability ({len(samples)*2} judgments)…")
    ind = await run_indist(samples)
    acc = accuracy(ind)
    lo, hi = wilson_ci(ind.total, ind.correct)

    print("  → style similarity…")
    sim = style_similarity_scores([{"history": s["history"], "model": s["model"]} for s in samples])

    print("  → relevance…")
    rel = await relevance_scores([{"incoming": s["incoming"], "model": s["model"]} for s in samples])

    return {
        "indistinguishability": {
            "accuracy": acc,
            "ci95_low": lo,
            "ci95_high": hi,
            "total": ind.total,
            "correct": ind.correct,
            "oracle_first_acc": ind.correct_oracle_first / ind.total_oracle_first if ind.total_oracle_first else None,
            "oracle_second_acc": ind.correct_oracle_second / ind.total_oracle_second if ind.total_oracle_second else None,
        },
        "style_similarity": sim,
        "relevance": rel,
    }


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=50, help="Eval sample cap (per baseline)")
    p.add_argument("--models", default="zero_shot,few_shot,fine_tuned")
    args = p.parse_args()

    test = [json.loads(l) for l in TEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not test:
        raise SystemExit("test_raw.jsonl is empty - run dataset/build_jsonl.py first")

    chosen = [m.strip() for m in args.models.split(",") if m.strip()]
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "test_size": len(test), "results": {}}

    for name in chosen:
        if name not in BASELINES:
            print(f"unknown baseline {name}; skipping")
            continue
        report["results"][name] = await evaluate_one(name, BASELINES[name], test, args.limit)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "eval_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (RESULTS_DIR / "eval_report.md").write_text(_to_markdown(report))
    _write_csv(report, RESULTS_DIR / "eval_report.csv")
    print(f"\nSaved → {RESULTS_DIR / 'eval_report.json'}")
    print(f"Saved → {RESULTS_DIR / 'eval_report.csv'}")


def _write_csv(report: dict, path: Path) -> None:
    import csv

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "model",
                "indist_accuracy",
                "ci95_low",
                "ci95_high",
                "indist_total",
                "oracle_first_acc",
                "oracle_second_acc",
                "style_sim_mean",
                "style_sim_std",
                "relevance_mean",
                "relevance_std",
            ]
        )
        for name, r in report["results"].items():
            ind, sim, rel = r["indistinguishability"], r["style_similarity"], r["relevance"]
            w.writerow(
                [
                    name,
                    f"{ind['accuracy']:.4f}",
                    f"{ind['ci95_low']:.4f}",
                    f"{ind['ci95_high']:.4f}",
                    ind["total"],
                    f"{ind['oracle_first_acc']:.4f}" if ind["oracle_first_acc"] is not None else "",
                    f"{ind['oracle_second_acc']:.4f}" if ind["oracle_second_acc"] is not None else "",
                    f"{sim['mean']:.4f}",
                    f"{sim['std']:.4f}",
                    f"{rel['mean']:.4f}",
                    f"{rel['std']:.4f}",
                ]
            )


def _to_markdown(report: dict) -> str:
    lines = ["# Gaia AI - Evaluation Report", ""]
    lines.append(f"- Created: {report['created_at']}")
    lines.append(f"- Test size: {report['test_size']}")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append(
        "| Model | Indist. Acc | 95% CI | Style Sim | Relevance |\n|---|---|---|---|---|"
    )
    for name, r in report["results"].items():
        ind = r["indistinguishability"]
        sim = r["style_similarity"]
        rel = r["relevance"]
        lines.append(
            f"| {name} | {ind['accuracy']:.2%} | [{ind['ci95_low']:.2%}, {ind['ci95_high']:.2%}] | "
            f"{sim['mean']:.3f} ± {sim['std']:.3f} | {rel['mean']:.2f} ± {rel['std']:.2f} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- **Indistinguishability accuracy ≈ 50%** = the LLM judge cannot reliably tell our model's responses from the oracle's; this is the SUCCESS condition (per spec §33 and lecturer feedback).")
    lines.append("- **Style similarity** (cosine in a multilingual embedding space) is a complementary metric; higher is stylistically closer to the user.")
    lines.append("- **Relevance** ensures the response actually addresses the message (style without content is not useful).")
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(main())
