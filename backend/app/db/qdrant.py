"""Qdrant client wrapper. One collection per user for style memory."""
from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings

_client: AsyncQdrantClient | None = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
    return _client


def user_collection(user_id: int) -> str:
    return f"user_{user_id}_style"


async def ensure_user_collection(user_id: int, dim: int | None = None) -> None:
    client = get_qdrant()
    col = user_collection(user_id)
    dim = dim or settings.EMBEDDING_DIM
    existing = {c.name for c in (await client.get_collections()).collections}
    if col not in existing:
        await client.create_collection(
            collection_name=col,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )


async def reset_user_collection(user_id: int, dim: int | None = None) -> None:
    """Delete and recreate the user's collection — used to re-embed from scratch
    (also handles an embedding-dimension change)."""
    client = get_qdrant()
    col = user_collection(user_id)
    try:
        await client.delete_collection(collection_name=col)
    except Exception:  # noqa: BLE001 - may not exist yet
        pass
    await client.create_collection(
        collection_name=col,
        vectors_config=VectorParams(size=dim or settings.EMBEDDING_DIM, distance=Distance.COSINE),
    )
