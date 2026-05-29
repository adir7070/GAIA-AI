"""Embedding-based style similarity.

For each test sample, compute cosine similarity between the model's response
embedding and the average embedding of the user's history. Higher = more
stylistically similar. Reported as mean ± std over the test set.
"""
from __future__ import annotations

import os

import numpy as np
from sentence_transformers import SentenceTransformer

# The synthetic dataset is bilingual (Hebrew + English), so we default to a
# MULTILINGUAL sentence embedder rather than the English-only bge-large-en —
# an English-only model under-represents Hebrew style and biases the metric.
# Override with STYLE_EMBED_MODEL if a different model is desired.
DEFAULT_EMBED_MODEL = "intfloat/multilingual-e5-large"
EMBED_MODEL = os.getenv("STYLE_EMBED_MODEL", DEFAULT_EMBED_MODEL)

_model: SentenceTransformer | None = None


def _embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a) + 1e-9
    nb = np.linalg.norm(b) + 1e-9
    return float(np.dot(a, b) / (na * nb))


def style_similarity_scores(samples: list[dict]) -> dict:
    """`samples`: list of {history, model}."""
    model = _embedder()
    sims = []
    for s in samples:
        if not s["history"] or not s.get("model"):
            continue
        h_emb = model.encode(s["history"], normalize_embeddings=True)
        h_mean = np.array(h_emb).mean(axis=0)
        m_emb = np.array(model.encode(s["model"], normalize_embeddings=True))
        sims.append(cosine(h_mean, m_emb))
    if not sims:
        return {"mean": 0.0, "std": 0.0, "n": 0}
    return {"mean": float(np.mean(sims)), "std": float(np.std(sims)), "n": len(sims)}
