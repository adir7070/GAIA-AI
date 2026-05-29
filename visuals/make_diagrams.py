"""Generate the project's static diagrams (no external deps beyond matplotlib).

Outputs (PNG, 200 dpi) into visuals/:
  - architecture.png     : system architecture (product + research planes)
  - pipeline.png         : ML research pipeline (synthetic -> dataset -> train -> eval)
  - visual_abstract.png  : one-glance problem -> method -> metric -> outcome

Run:  python visuals/make_diagrams.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent

# palette
NAVY = "#10243e"
BLUE = "#2b6cb0"
GREEN = "#2f855a"
ORANGE = "#dd6b20"
PURPLE = "#6b46c1"
GREY = "#4a5568"
LIGHT = "#edf2f7"


def _box(ax, x, y, w, h, text, fc, ec=None, tc="white", fs=11, bold=True):
    ec = ec or fc
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            linewidth=1.5, edgecolor=ec, facecolor=fc,
        )
    )
    ax.text(
        x + w / 2, y + h / 2, text,
        ha="center", va="center", color=tc, fontsize=fs,
        fontweight="bold" if bold else "normal", wrap=True,
    )


def _arrow(ax, x1, y1, x2, y2, color=GREY, style="-|>", lw=1.8):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle=style, mutation_scale=16,
            linewidth=lw, color=color, shrinkA=2, shrinkB=2,
        )
    )


def _canvas(w=12, h=7):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


# --------------------------------------------------------------------------- #
def architecture():
    fig, ax = _canvas(12, 7.2)
    ax.text(50, 96, "Gaia AI — System Architecture", ha="center", fontsize=17, fontweight="bold", color=NAVY)
    ax.text(50, 91, "Product plane (real-time suggestions) + Research plane (offline training)",
            ha="center", fontsize=10, color=GREY)

    # product plane
    _box(ax, 6, 78, 22, 8, "Frontend\nNext.js 14 (RTL he/en)", BLUE)
    _box(ax, 39, 78, 22, 8, "Backend API\nFastAPI + Celery", NAVY)
    _box(ax, 72, 78, 22, 8, "WhatsApp Bridge\nNode + whatsapp-web.js", GREEN)

    _arrow(ax, 28, 82, 39, 82); ax.text(33.5, 84, "REST/WS\n(JWT)", ha="center", fontsize=7, color=GREY)
    _arrow(ax, 61, 82, 72, 82); ax.text(66.5, 84, "HMAC\nwebhook", ha="center", fontsize=7, color=GREY)
    _arrow(ax, 83, 78, 83, 70); ax.text(89, 74, "QR / events", ha="center", fontsize=7, color=GREY)
    _box(ax, 72, 62, 22, 7, "WhatsApp Web", GREY)

    # data stores
    for i, (lbl, c) in enumerate([
        ("Postgres\nusers/contacts", NAVY), ("MongoDB\nmessages/outputs", GREEN),
        ("Qdrant\nstyle vectors", PURPLE), ("Redis\nqueue/cache", ORANGE),
    ]):
        _box(ax, 6 + i * 23, 50, 20, 8, lbl, c, fs=9)
        _arrow(ax, 50, 78, 16 + i * 23, 58, color="#a0aec0", lw=1.0)

    # research plane
    ax.add_patch(FancyBboxPatch((6, 12), 88, 30, boxstyle="round,pad=0.3,rounding_size=0.6",
                                linewidth=1.5, edgecolor=PURPLE, facecolor=LIGHT))
    ax.text(50, 38.5, "Research plane (ml/) — offline, on cloud GPU", ha="center", fontsize=11,
            fontweight="bold", color=PURPLE)
    stages = [
        ("Synthetic\npersonas+pairs", ORANGE),
        ("Dataset\ntrain/val/test", BLUE),
        ("QLoRA\nfine-tune\nLlama-3-8B", GREEN),
        ("Eval\nIndistinguish.", PURPLE),
    ]
    for i, (lbl, c) in enumerate(stages):
        _box(ax, 9 + i * 21.5, 19, 18, 12, lbl, c, fs=9.5)
        if i:
            _arrow(ax, 9 + i * 21.5 - 3.5, 25, 9 + i * 21.5, 25)  # left -> right flow
    _arrow(ax, 60, 62, 60, 42, color=PURPLE, lw=1.2)
    ax.text(63, 52, "trained adapter\nserves suggestions", fontsize=7, color=PURPLE)

    fig.tight_layout()
    fig.savefig(OUT / "architecture.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def pipeline():
    fig, ax = _canvas(13, 4.6)
    ax.text(50, 92, "Gaia AI — Research Pipeline", ha="center", fontsize=16, fontweight="bold", color=NAVY)
    steps = [
        ("1. Diversity matrix\n→ hidden style seeds", ORANGE),
        ("2. Personas +\nhistories (LLM)", ORANGE),
        ("3. (history, incoming,\noracle target) pairs", BLUE),
        ("4. Build splits\nper-user 80/10/10", BLUE),
        ("5. QLoRA fine-tune\nLlama-3-8B (NF4)", GREEN),
        ("6. Eval: zero/few-shot\nvs fine-tuned vs oracle", PURPLE),
    ]
    w = 14.5
    for i, (lbl, c) in enumerate(steps):
        x = 2 + i * 16
        _box(ax, x, 40, w, 26, lbl, c, fs=8.6)
        if i:
            _arrow(ax, x - 1.5, 53, x, 53)
    ax.text(50, 30, "Headline metric: Style-Indistinguishability — LLM judge accuracy ≈ 50% = success",
            ha="center", fontsize=9.5, color=NAVY, style="italic")
    ax.text(50, 22, "Outputs: data/synthetic/*.jsonl · results/eval_report.{json,md,csv} · figures",
            ha="center", fontsize=8.5, color=GREY)
    fig.tight_layout()
    fig.savefig(OUT / "pipeline.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def visual_abstract():
    fig, ax = _canvas(12, 6.6)
    ax.text(50, 95, "Gaia AI — Visual Abstract", ha="center", fontsize=17, fontweight="bold", color=NAVY)
    ax.text(50, 90,
            "Personalized response generation via implicit user-style learning",
            ha="center", fontsize=11, color=GREY, style="italic")

    panels = [
        ("PROBLEM", ORANGE,
         "Reproduce a person's WhatsApp\nwriting style and answer new\nmessages in that style.\nNo labeled style data exists."),
        ("DATA", BLUE,
         "Generate synthetic users with\nHIDDEN style seeds (diversity\nmatrix). Oracle LLM writes\ntarget replies. ~hundreds–50k\n(history, incoming, target) triples."),
        ("METHOD", GREEN,
         "Fine-tune Llama-3-8B with\nQLoRA (NF4, r=16, α=32) to\nlearn style IMPLICITLY.\nCompare vs zero-shot & few-shot\noff-the-shelf baselines."),
        ("METRIC & GOAL", PURPLE,
         "Style-Indistinguishability:\nan LLM judge guesses model vs\nuser reply. Accuracy → 50%\n(chance) = indistinguishable.\n+ style-similarity & relevance."),
    ]
    for i, (title, c, body) in enumerate(panels):
        x = 4 + i * 23.5
        _box(ax, x, 58, 20, 10, title, c, fs=12)
        ax.add_patch(FancyBboxPatch((x, 20), 20, 34, boxstyle="round,pad=0.2,rounding_size=0.4",
                                    linewidth=1.4, edgecolor=c, facecolor="white"))
        ax.text(x + 10, 37, body, ha="center", va="center", fontsize=8.2, color=NAVY)
        if i:
            _arrow(ax, x - 3.5, 44, x, 44, color=GREY)

    ax.text(50, 11, "Human-in-the-loop: the system SUGGESTS; it never auto-sends.",
            ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "visual_abstract.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    architecture()
    pipeline()
    visual_abstract()
    print("Wrote:", *(p.name for p in sorted(OUT.glob("*.png"))))
