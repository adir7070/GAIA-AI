"""Interim deck (Week 9) — structure per requirements 1023:
Project review · Previous work (>=3 papers) · Dataset + EDA · Baseline solution & results · Plan.
"""
from __future__ import annotations

from content._data import eda_stats, results_table_rows


def _dataset_bullets():
    s = eda_stats() or {}
    b = [
        "Synthetic dataset generated with an LLM (Self-Instruct-style), bilingual he/en.",
        "Each user has a HIDDEN style seed from a 10-axis diversity matrix; targets written by an oracle that sees the seed.",
        "Splits are PER-USER (no user in both train and test) → tests generalization to unseen people.",
    ]
    if s:
        b.append((1, f"Scale: {s.get('n_personas','?')} personas · {s.get('n_histories','?')} histories · {s.get('n_pairs','?')} (history, incoming, target) pairs."))
        if s.get("target_len_chars"):
            t = s["target_len_chars"]
            b.append((1, f"Target reply length: mean {t['mean']} chars (median {t['median']}, range {t['min']}–{t['max']})."))
        if s.get("history_msg_len_chars"):
            h = s["history_msg_len_chars"]
            b.append((1, f"History message length: mean {h['mean']} chars over {h['n_messages']} messages."))
    else:
        b.append((1, "EDA stats fill in automatically after running ml/eda/run_eda.py."))
    return b


def build() -> dict:
    rows, available = results_table_rows()
    baseline_note = ("Real baseline numbers (zero/few-shot via Groq). fine_tuned = run on GPU."
                     if available else "Numbers populate after running eval.run_all.")
    return {
        "slides": [
            {
                "kind": "title",
                "title": "Gaia AI — Interim Report",
                "subtitle": "Dataset, EDA & baseline · Adir · LLM course (HIT)",
            },
            {
                "title": "1 · Project Review",
                "bullets": [
                    "Goal: generate WhatsApp replies in a user's own implicit style, from their chat history.",
                    "Changed from proposal: added a MULTILINGUAL style-similarity embedder (data is he+en); hardened synthetic generation.",
                    "Novelty/contribution:",
                    (1, "Implicit style learning (no tone labels) from synthetic personas with hidden seeds."),
                    (1, "Evaluation by Style-Indistinguishability (LLM judge → 50%) rather than a soft similarity score."),
                ],
                "image": "visuals/visual_abstract.png",
            },
            {
                "title": "2 · Previous Work",
                "bullets": ["Reviewed across our four pillars (full table + citations in docs/related_work.md):"],
                "table": {
                    "headers": ["Paper (year)", "Task", "Relation to us"],
                    "rows": [
                        ["QLoRA (2023)", "4-bit LoRA fine-tuning", "Our exact training method"],
                        ["Self-Instruct (2023)", "LLM-generated training data", "Our synthetic-data strategy"],
                        ["LLM-as-a-Judge (2023)", "LLM eval + biases", "Basis of our indistinguishability metric"],
                        ["LaMP (2024)", "Personalization benchmark", "We learn style implicitly, not via retrieval"],
                        ["PersonaChat (2018)", "Persona-grounded dialogue", "We use implicit, not explicit, personas"],
                    ],
                },
                "note": "Recent, high-citation works (NeurIPS/ACL). arXiv IDs in docs/related_work.md.",
            },
            {
                "title": "3 · Dataset & EDA",
                "bullets": _dataset_bullets(),
                "image": "visuals/eda/lang_dist.png",
            },
            {
                "title": "3b · EDA — length & style distributions",
                "bullets": [
                    "Style axes are spread across the diversity matrix (formality, emoji, slang, length).",
                    "Message and target-reply lengths skew short, matching real WhatsApp behavior.",
                ],
                "image": "visuals/eda/target_len.png",
            },
            {
                "title": "4 · Baseline Solution & Results",
                "bullets": [
                    "Baselines (off-the-shelf, no fine-tune): zero-shot and few-shot prompting on Llama-3.x via Groq.",
                    "Oracle = upper bound (LLM that saw the hidden seed).",
                    "Evaluated on the held-out per-user test split with all three metrics.",
                ],
                "table": {"headers": ["Model", "Indist.", "95% CI", "StyleSim", "Relev."], "rows": rows},
                "image": "visuals/results/indist_accuracy.png",
                "note": baseline_note,
            },
            {
                "title": "5 · Plan",
                "bullets": ["Remaining steps to the final report:"],
                "table": {
                    "headers": ["Step", "Scope", "Expected outcome"],
                    "rows": [
                        ["Fine-tune", "QLoRA Llama-3-8B on cloud GPU (Modal/RunPod)", "Trained adapter"],
                        ["Re-eval", "Add fine_tuned column vs baselines", "Full comparison table"],
                        ["Scale data", "More users (paid Groq tier / multi-day)", "More robust numbers"],
                        ["Error analysis", "Inspect bad cases, tune prompts", "Quality improvements"],
                        ["Final deck", "Results + conclusions", "Submission"],
                    ],
                },
            },
        ]
    }
