"""Turn ml/results/eval_report.json into result figures (offline, no API calls).

Outputs to visuals/results/:
  - indist_accuracy.png   : per-model indistinguishability accuracy + 95% CI, 50% target line
  - style_similarity.png  : per-model style similarity (mean ± std)
  - relevance.png         : per-model relevance (mean ± std)
  - results_table.png     : rendered summary table

Run:  python ml/eval/plots.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "ml" / "results" / "eval_report.json"
OUT = ROOT / "visuals" / "results"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#10243e"
COLORS = {"zero_shot": "#dd6b20", "few_shot": "#2b6cb0", "fine_tuned": "#2f855a", "oracle": "#6b46c1"}


def _load():
    if not REPORT.exists():
        raise SystemExit(f"{REPORT} not found - run eval.run_all first")
    return json.loads(REPORT.read_text(encoding="utf-8"))


def indist_plot(rep):
    models = list(rep["results"].keys())
    acc = [rep["results"][m]["indistinguishability"]["accuracy"] * 100 for m in models]
    lo = [rep["results"][m]["indistinguishability"]["ci95_low"] * 100 for m in models]
    hi = [rep["results"][m]["indistinguishability"]["ci95_high"] * 100 for m in models]
    err = [[a - l for a, l in zip(acc, lo)], [h - a for h, a in zip(hi, acc)]]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(models, acc, yerr=err, capsize=6,
                  color=[COLORS.get(m, "#888") for m in models])
    ax.axhline(50, ls="--", color="crimson", lw=1.5)
    ax.text(len(models) - 0.5, 51.5, "50% = indistinguishable (target)", color="crimson", fontsize=9, ha="right")
    ax.set_ylabel("Judge accuracy (%)")
    ax.set_title("Style Indistinguishability (lower → closer to 50% = better)",
                 fontsize=12, fontweight="bold", color=NAVY)
    ax.set_ylim(0, 100)
    for b, a in zip(bars, acc):
        ax.text(b.get_x() + b.get_width() / 2, a + 3, f"{a:.0f}%", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "indist_accuracy.png", dpi=170)
    plt.close(fig)


def _mean_std_plot(rep, key, title, fname, ylim=None):
    models = list(rep["results"].keys())
    mean = [rep["results"][m][key]["mean"] for m in models]
    std = [rep["results"][m][key]["std"] for m in models]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(models, mean, yerr=std, capsize=6, color=[COLORS.get(m, "#888") for m in models])
    ax.set_title(title, fontsize=12, fontweight="bold", color=NAVY)
    if ylim:
        ax.set_ylim(*ylim)
    for i, m in enumerate(mean):
        ax.text(i, m, f"{m:.2f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=170)
    plt.close(fig)


def table_plot(rep):
    models = list(rep["results"].keys())
    headers = ["Model", "Indist. Acc", "95% CI", "Style Sim", "Relevance"]
    rows = []
    for m in models:
        r = rep["results"][m]
        ind, sim, rel = r["indistinguishability"], r["style_similarity"], r["relevance"]
        rows.append([m, f"{ind['accuracy']*100:.1f}%",
                     f"[{ind['ci95_low']*100:.0f}, {ind['ci95_high']*100:.0f}]%",
                     f"{sim['mean']:.3f} ± {sim['std']:.3f}",
                     f"{rel['mean']:.2f} ± {rel['std']:.2f}"])
    fig, ax = plt.subplots(figsize=(9, 1.2 + 0.5 * len(rows)))
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1, 1.6)
    for j in range(len(headers)):
        c = t[0, j]; c.set_facecolor(NAVY); c.set_text_props(color="white", fontweight="bold")
    ax.set_title(f"Evaluation results (test size = {rep.get('test_size','?')})",
                 fontsize=12, fontweight="bold", color=NAVY, pad=14)
    fig.tight_layout()
    fig.savefig(OUT / "results_table.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    rep = _load()
    indist_plot(rep)
    _mean_std_plot(rep, "style_similarity", "Style similarity (cosine, multilingual embedder)",
                   "style_similarity.png", ylim=(0, 1))
    _mean_std_plot(rep, "relevance", "Relevance (LLM judge, 1–5)", "relevance.png", ylim=(0, 5))
    table_plot(rep)
    print(f"Wrote result figures → {OUT}")


if __name__ == "__main__":
    main()
