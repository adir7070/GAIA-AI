"""Vector retrieval for user-specific style memory."""
from __future__ import annotations

import uuid
from typing import Any

from qdrant_client.http.models import PointStruct

from app.db.qdrant import ensure_user_collection, get_qdrant, user_collection
from app.services.embeddings import embed, embed_batch


async def add_messages(user_id: int, messages: list[dict[str, Any]]) -> int:
    """Bulk-add messages (text + meta) to the user's style collection."""
    if not messages:
        return 0
    await ensure_user_collection(user_id)
    texts = [m["text"] for m in messages]
    vectors = await embed_batch(texts)

    points = [
        PointStruct(
            id=m.get("id") or str(uuid.uuid4()),
            vector=v,
            payload={
                "text": m["text"],
                "ts": m.get("ts"),
                "wa_id": m.get("wa_id"),
                "direction": m.get("direction"),
            },
        )
        for m, v in zip(messages, vectors)
    ]
    qdr = get_qdrant()
    await qdr.upsert(collection_name=user_collection(user_id), points=points)
    return len(points)


async def retrieve_similar(user_id: int, query: str, top_k: int = 12) -> list[dict[str, Any]]:
    await ensure_user_collection(user_id)
    qvec = await embed(query)
    qdr = get_qdrant()
    res = await qdr.search(
        collection_name=user_collection(user_id),
        query_vector=qvec,
        limit=top_k,
        with_payload=True,
    )
    return [{"text": r.payload.get("text", ""), "score": r.score, **r.payload} for r in res]
