"""Embedding service. BGE-large by default (CPU/GPU local) with OpenAI fallback."""
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
    """Embed a single text. Sync model is fine on small batches; for hot paths use a worker."""
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from openai import AsyncOpenAI

        cli = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        r = await cli.embeddings.create(model=settings.OPENAI_EMBED_MODEL, input=[text])
        return r.data[0].embedding

    vec = _local_model().encode(text, normalize_embeddings=True).tolist()
    return list(vec)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from openai import AsyncOpenAI

        cli = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        r = await cli.embeddings.create(model=settings.OPENAI_EMBED_MODEL, input=texts)
        return [d.embedding for d in r.data]

    vecs = _local_model().encode(texts, normalize_embeddings=True)
    return [list(v) for v in vecs]
