"""Proposal deck (Week 5) — structure per course requirements 1023:
Motivating use case · Task description · Models & methods · Data spec & generation · Metrics & KPIs.
"""
from __future__ import annotations


def build() -> dict:
    return {
        "slides": [
            {
                "kind": "title",
                "title": "Gaia AI — Project Proposal",
                "subtitle": "Personalized response generation via implicit user-style learning · Adir · LLM course (HIT)",
            },
            {
                "title": "1 · Motivating Use Case",
                "bullets": [
                    "Communication-heavy people (educators, consultants, founders, support) get floods of messages whose replies follow a consistent PERSONAL style.",
                    "Today this is solved by typing every reply manually, or by generic auto-replies that sound nothing like the user.",
                    (1, "Why important: time cost is huge and tone consistency matters for relationships/brand."),
                    (1, "Why hard: a person's style is implicit — sentence length, emoji, slang, punctuation, rhythm — and there is NO labeled 'style' dataset."),
                    "Gaia AI learns the user's style from their own chat history and SUGGESTS replies (never auto-sends — human approves).",
                ],
                "image": "visuals/visual_abstract.png",
            },
            {
                "title": "2 · Project Task Description",
                "bullets": [
                    "Formal problem: conditional text generation with implicit style conditioning.",
                    (1, "Input: a user's chat history + a new incoming message."),
                    (1, "Output: a reply that (a) addresses the message and (b) preserves the user's implicit writing style."),
                    "Novelty: learn style IMPLICITLY (no tone labels) and evaluate by Style-Indistinguishability instead of a soft similarity score.",
                    "Scope is novel & data-free: no public dataset exists → we generate synthetic training and test data.",
                ],
            },
            {
                "title": "3 · Models & Methods",
                "bullets": [
                    "Pipeline: diversity matrix → synthetic personas+histories → (history, incoming, oracle-target) pairs → splits → fine-tune → eval.",
                    "Fine-tuned model: Llama-3-8B-Instruct + QLoRA (4-bit NF4, r=16, α=32, target q/k/v/o).",
                    "Off-the-shelf baselines to compare against:",
                    (1, "Zero-shot prompting (style instruction only)."),
                    (1, "Few-shot prompting (5–8 history examples in context)."),
                    (1, "Oracle (LLM that saw the hidden style seed) = upper bound."),
                    "Style memory retrieval (embeddings/Qdrant) provides relevant history at runtime.",
                ],
                "image": "visuals/pipeline.png",
            },
            {
                "title": "4 · Data Specification & Generation",
                "bullets": [
                    "No real labeled data → generate SYNTHETIC data with an LLM (Self-Instruct-style).",
                    "Each synthetic user gets a HIDDEN style seed sampled from a diversity matrix:",
                    (1, "language (he/en) × length × emoji × slang × formality × rhythm × punctuation × greeting × occupation × age."),
                    "Per user: ~30–50 style-reference messages + (history, incoming, target) triples; target written by an 'oracle' that sees the seed.",
                    "Splits are PER-USER (no user in both train and test) to test generalization to unseen people.",
                    "Real data (optional, evaluation only): opt-in, anonymized, AES-encrypted, gitignored.",
                ],
            },
            {
                "title": "5 · Metrics & KPIs",
                "bullets": [
                    "Headline — Style-Indistinguishability: an LLM judge sees history+incoming+two replies (oracle vs ours, randomized) and guesses the user's.",
                    (1, "KPI: judge accuracy → 50% (chance) = indistinguishable = success."),
                    (1, "Report 95% Wilson CI + order-bias check; judge model separated from generator."),
                    "Style similarity: cosine in a MULTILINGUAL embedding space vs the user's history (he+en).",
                    "Relevance: LLM 1–5 — does the reply actually address the message? (style without content is useless).",
                    "Quality protocol: per-user split, bias mitigations, ground-truth = oracle (synthetic) / real user (real test).",
                ],
                "note": "Targets: fine_tuned indist. ∈ [45%,55%]; baselines higher (judge can spot them).",
            },
        ]
    }
