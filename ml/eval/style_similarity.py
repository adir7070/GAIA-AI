"""Embedding-based style similarity.

For each test sample, compute cosine similarity between the model's response
embedding and the average embedding of the user's history. Higher = more
stylistically similar. Reported as mean ± std over the test set.
"""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


_model: SentenceTransformer | None = None


def _embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-large-en-v1.5")
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
