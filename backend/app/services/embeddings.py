"""Embedding service — always uses the local sentence-transformers model.

The embedding model (for vector search) is intentionally decoupled from the
LLM provider (for text generation). Switching LLM_PROVIDER to openai/groq does
NOT change the embedding model, so Qdrant collections stay compatible.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _local_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL)


async def embed(text: str) -> list[float]:
    vec = _local_model().encode(text, normalize_embeddings=True).tolist()
    return list(vec)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    vecs = _local_model().encode(texts, normalize_embeddings=True)
    return [list(v) for v in vecs]
