"""Helpers so deck content can pull LIVE numbers from the pipeline outputs.

If the JSON outputs don't exist yet, callers fall back to a 'pending' string so
the decks still build before the experiment has been run.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "ml" / "results" / "eval_report.json"
EDA = ROOT / "results" / "eda_stats.json"


def eval_report() -> dict | None:
    if EVAL.exists():
        try:
            return json.loads(EVAL.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def eda_stats() -> dict | None:
    if EDA.exists():
        try:
            return json.loads(EDA.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def results_table_rows():
    """Return (rows, available) for the eval results table."""
    rep = eval_report()
    if not rep:
        return [["zero_shot", "pending", "pending", "pending"],
                ["few_shot", "pending", "pending", "pending"],
                ["fine_tuned", "GPU run", "—", "—"]], False
    rows = []
    for name, r in rep["results"].items():
        ind, sim, rel = r["indistinguishability"], r["style_similarity"], r["relevance"]
        rows.append([
            name,
            f"{ind['accuracy']*100:.1f}%",
            f"[{ind['ci95_low']*100:.0f},{ind['ci95_high']*100:.0f}]%",
            f"{sim['mean']:.3f}",
            f"{rel['mean']:.2f}",
        ])
    if "fine_tuned" not in rep["results"]:
        rows.append(["fine_tuned", "pending (GPU)", "—", "—", "—"])
    return rows, True
