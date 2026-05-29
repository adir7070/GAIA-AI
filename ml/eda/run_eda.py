"""Exploratory Data Analysis for the synthetic dataset (offline, no API calls).

Reads ml/data/synthetic/{personas,histories,pairs}.jsonl and writes:
  - visuals/eda/*.png   (figures)
  - results/eda_stats.json   (summary statistics, used by README + slides)

Run:  python ml/eda/run_eda.py
"""
from __future__ import annotations

import json
import statistics as st
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
SYN = ROOT / "ml" / "data" / "synthetic"
FIG = ROOT / "visuals" / "eda"
STATS = ROOT / "results" / "eda_stats.json"
FIG.mkdir(parents=True, exist_ok=True)
STATS.parent.mkdir(parents=True, exist_ok=True)

NAVY = "#10243e"
BLUE = "#2b6cb0"
GREEN = "#2f855a"
ORANGE = "#dd6b20"


def _load(name):
    p = SYN / name
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _bar(counter, title, fname, color=BLUE, rotate=0):
    if not counter:
        return
    keys = list(counter.keys())
    vals = [counter[k] for k in keys]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(range(len(keys)), vals, color=color)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(keys, rotation=rotate, ha="right" if rotate else "center", fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold", color=NAVY)
    ax.set_ylabel("count")
    for i, v in enumerate(vals):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / fname, dpi=160)
    plt.close(fig)


def _hist(values, title, fname, xlabel, color=GREEN, bins=20):
    if not values:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(values, bins=bins, color=color, edgecolor="white")
    ax.set_title(title, fontsize=12, fontweight="bold", color=NAVY)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(FIG / fname, dpi=160)
    plt.close(fig)


def main():
    personas = _load("personas.jsonl")
    histories = _load("histories.jsonl")
    pairs = _load("pairs.jsonl")

    stats: dict = {"n_personas": len(personas), "n_histories": len(histories), "n_pairs": len(pairs)}

    # --- style-axis distributions (from hidden seeds) ---
    axes = ["language", "avg_length", "emoji", "slang", "formality", "rhythm"]
    axis_counts = {a: Counter() for a in axes}
    for p in personas:
        hs = p.get("hidden_style", {})
        for a in axes:
            if hs.get(a) is not None:
                axis_counts[a][hs[a]] += 1
    _bar(axis_counts["language"], "Language distribution (personas)", "lang_dist.png", BLUE)
    _bar(axis_counts["formality"], "Formality distribution", "formality_dist.png", ORANGE, rotate=30)
    _bar(axis_counts["emoji"], "Emoji-usage distribution", "emoji_dist.png", GREEN, rotate=20)
    _bar(axis_counts["avg_length"], "Style length-bucket distribution", "length_bucket_dist.png", BLUE, rotate=20)
    _bar(axis_counts["slang"], "Slang distribution", "slang_dist.png", ORANGE, rotate=20)
    stats["style_axes"] = {a: dict(c) for a, c in axis_counts.items()}

    # --- message length distributions ---
    hist_msg_lens = [len(m) for h in histories for m in h.get("messages", [])]
    _hist(hist_msg_lens, "History message length (chars)", "hist_msg_len.png", "characters per message", GREEN)
    if hist_msg_lens:
        stats["history_msg_len_chars"] = {
            "mean": round(st.mean(hist_msg_lens), 1),
            "median": st.median(hist_msg_lens),
            "min": min(hist_msg_lens), "max": max(hist_msg_lens),
            "n_messages": len(hist_msg_lens),
        }

    tgt_lens = [len(p.get("target_response", "")) for p in pairs]
    _hist(tgt_lens, "Target response length (chars)", "target_len.png", "characters", ORANGE)
    inc_lens = [len(p.get("incoming_message", "")) for p in pairs]
    _hist(inc_lens, "Incoming message length (chars)", "incoming_len.png", "characters", BLUE)
    if tgt_lens:
        stats["target_len_chars"] = {"mean": round(st.mean(tgt_lens), 1), "median": st.median(tgt_lens),
                                     "min": min(tgt_lens), "max": max(tgt_lens)}

    # --- pairs per user ---
    per_user = Counter(p["user_id"] for p in pairs)
    if per_user:
        _hist(list(per_user.values()), "Pairs per user", "pairs_per_user.png", "pairs", BLUE,
              bins=max(5, len(set(per_user.values()))))
        stats["pairs_per_user"] = {"mean": round(st.mean(per_user.values()), 1),
                                   "min": min(per_user.values()), "max": max(per_user.values()),
                                   "n_users_with_pairs": len(per_user)}

    # --- words per history message ---
    word_counts = [len(m.split()) for h in histories for m in h.get("messages", [])]
    _hist(word_counts, "History message length (words)", "hist_msg_words.png", "words per message", GREEN, bins=15)

    STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    figs = sorted(p.name for p in FIG.glob("*.png"))
    print(f"EDA: {stats['n_personas']} personas, {stats['n_histories']} histories, {stats['n_pairs']} pairs")
    print(f"Wrote {len(figs)} figures → {FIG}")
    print(f"Wrote stats → {STATS}")


if __name__ == "__main__":
    main()
