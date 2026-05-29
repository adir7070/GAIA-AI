"""Final deck (Week 13) — structure per requirements 1023:
Refined definition · Achievements & novelty · Methodology · Results · Conclusion + future work.
"""
from __future__ import annotations

from content._data import eval_report, results_table_rows


def _results_bullets():
    rep = eval_report()
    if not rep:
        return ["Run eval.run_all + ml/eval/plots.py to populate real numbers and figures."]
    out = [f"Evaluated on a held-out per-user test split (test size = {rep.get('test_size','?')})."]
    res = rep["results"]
    if "zero_shot" in res and "few_shot" in res:
        z = res["zero_shot"]["indistinguishability"]["accuracy"] * 100
        f = res["few_shot"]["indistinguishability"]["accuracy"] * 100
        out.append(f"Off-the-shelf baselines — zero-shot indist. {z:.0f}%, few-shot {f:.0f}% (closer to 50% = better).")
    out.append("fine_tuned column is filled after the QLoRA GPU run (Modal/RunPod) — the core comparison.")
    return out


def build() -> dict:
    rows, _ = results_table_rows()
    return {
        "slides": [
            {
                "kind": "title",
                "title": "Gaia AI — Final Report",
                "subtitle": "Personalized response generation via implicit user-style learning · Adir · LLM course (HIT)",
            },
            {
                "title": "1 · Project Definition (refined)",
                "bullets": [
                    "Problem: given a user's chat history + a new message, generate a reply in the user's IMPLICIT style.",
                    "Models: fine-tuned Llama-3-8B (QLoRA) vs off-the-shelf zero-/few-shot; oracle = upper bound.",
                    "Data: synthetic, persona-conditioned, bilingual; per-user splits.",
                    "Metrics: Style-Indistinguishability (headline), style-similarity, relevance.",
                ],
                "image": "visuals/visual_abstract.png",
            },
            {
                "title": "2 · Achievements & Novelty",
                "bullets": [
                    "Built an end-to-end pipeline: diversity matrix → synthetic data → fine-tune → indistinguishability eval.",
                    "Generated a bilingual persona-conditioned dataset with hidden style seeds (no style labels leaked).",
                    "Produced real baseline results and a reproducible eval (JSON/MD/CSV + figures).",
                    "Novelty: implicit style learning + indistinguishability metric — distinct from retrieval-based personalization (LaMP) and explicit personas (PersonaChat).",
                ],
            },
            {
                "title": "3 · Methodology",
                "bullets": [
                    "Synthetic generation: LLM role-play with hidden seeds; oracle writes targets; robust JSON parsing.",
                    "Fine-tuning: QLoRA (4-bit NF4, r=16, α=32, target q/k/v/o) on Llama-3-8B-Instruct (cloud GPU).",
                    "Evaluation effort for quality:",
                    (1, "Per-user splits; order-randomized judge; judge model separated from generator."),
                    (1, "Multilingual embedder for he+en style similarity; relevance guards content."),
                    (1, "Rate-limit-aware generation (backoff, serialized) for reproducibility on free tiers."),
                ],
                "image": "visuals/pipeline.png",
            },
            {
                "title": "4 · Results",
                "bullets": _results_bullets(),
                "table": {"headers": ["Model", "Indist.", "95% CI", "StyleSim", "Relev."], "rows": rows},
                "image": "visuals/results/indist_accuracy.png",
                "note": "Indistinguishability ≈ 50% = success. Figures in visuals/results/.",
            },
            {
                "title": "5 · Conclusion & Future Work",
                "bullets": [
                    "The framework works end-to-end and yields real baseline numbers; fine-tuned arm is one GPU run away.",
                    "What I'd change: larger dataset (paid LLM tier), a stronger separate judge model, more error analysis.",
                    "Future: real opt-in data generalization test; RLHF from user edits; multi-personality switching.",
                    "Human-in-the-loop throughout — the system suggests; the user approves.",
                ],
            },
        ]
    }
