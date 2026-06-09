"""Vector memory for cloning the user 1:1.

The key object is a CONVERSATION PAIR: (their incoming message -> the user's
actual reply). We embed the incoming side and store the reply. At inference we
find pairs whose incoming is similar to the new message and show the model how
the user REALLY replied in those situations — so it mimics the user's actual
decisions, not just their generic style.
"""
from __future__ import annotations

import uuid
from typing import Any

from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.db.qdrant import ensure_user_collection, get_qdrant, user_collection
from app.services.embeddings import embed, embed_batch

# e5 models work best with these prefixes.
_Q = "query: "
_P = "passage: "


def user_pairs_collection(user_id: int) -> str:
    return f"user_{user_id}_pairs"


async def _ensure_pairs(user_id: int) -> None:
    client = get_qdrant()
    col = user_pairs_collection(user_id)
    existing = {c.name for c in (await client.get_collections()).collections}
    if col not in existing:
        await client.create_collection(
            collection_name=col,
            vectors_config=VectorParams(size=settings.EMBEDDING_DIM, distance=Distance.COSINE),
        )


async def reset_pairs_collection(user_id: int) -> None:
    client = get_qdrant()
    col = user_pairs_collection(user_id)
    try:
        await client.delete_collection(collection_name=col)
    except Exception:  # noqa: BLE001
        pass
    await client.create_collection(
        collection_name=col,
        vectors_config=VectorParams(size=settings.EMBEDDING_DIM, distance=Distance.COSINE),
    )


async def add_pairs(user_id: int, pairs: list[dict[str, Any]], *, manual: bool = False) -> int:
    """pairs: list of {incoming, reply}. Embeds the incoming side.
    manual=True marks the pair as explicitly taught by the user so it is
    always included in the prompt regardless of semantic similarity.
    """
    pairs = [p for p in pairs if p.get("incoming") and p.get("reply")]
    if not pairs:
        return 0
    await _ensure_pairs(user_id)
    vectors = await embed_batch([_P + p["incoming"] for p in pairs])
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=v,
            payload={
                "incoming": p["incoming"],
                "reply": p["reply"],
                "ts": p.get("ts"),
                "manual": manual,
            },
        )
        for p, v in zip(pairs, vectors)
    ]
    await get_qdrant().upsert(collection_name=user_pairs_collection(user_id), points=points)
    return len(points)


async def get_manual_pairs(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    """Return all manually-taught pairs (manual=True) with their point IDs."""
    await _ensure_pairs(user_id)
    client = get_qdrant()
    col = user_pairs_collection(user_id)
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    try:
        res, _ = await client.scroll(
            collection_name=col,
            scroll_filter=Filter(
                must=[FieldCondition(key="manual", match=MatchValue(value=True))]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
    except Exception:
        return []
    out = []
    for p in res:
        pl = p.payload or {}
        if pl.get("incoming") and pl.get("reply"):
            out.append({
                "id": str(p.id),
                "incoming": pl["incoming"],
                "reply": pl["reply"],
                "ts": pl.get("ts"),
            })
    return out


async def delete_pair(user_id: int, point_id: str) -> bool:
    """Delete a single pair by its Qdrant point ID."""
    await _ensure_pairs(user_id)
    try:
        from qdrant_client.http.models import PointIdsList
        await get_qdrant().delete(
            collection_name=user_pairs_collection(user_id),
            points_selector=PointIdsList(points=[point_id]),
        )
        return True
    except Exception:
        return False


async def retrieve_pairs(user_id: int, query: str, top_k: int = 8) -> list[dict[str, Any]]:
    await _ensure_pairs(user_id)
    qvec = await embed(_Q + query)
    res = await get_qdrant().query_points(
        collection_name=user_pairs_collection(user_id),
        query=qvec,
        limit=top_k,
        with_payload=True,
    )
    out = []
    for p in res.points:
        pl = p.payload or {}
        if pl.get("reply"):
            out.append({"incoming": pl.get("incoming", ""), "reply": pl["reply"], "score": p.score})
    return out


# ----- Legacy single-message style memory (kept for compatibility) ----------
async def add_messages(user_id: int, messages: list[dict[str, Any]]) -> int:
    if not messages:
        return 0
    await ensure_user_collection(user_id)
    texts = [m["text"] for m in messages]
    vectors = await embed_batch([_P + t for t in texts])
    points = [
        PointStruct(
            id=m.get("id") or str(uuid.uuid4()),
            vector=v,
            payload={"text": m["text"], "ts": m.get("ts"), "wa_id": m.get("wa_id"), "direction": m.get("direction")},
        )
        for m, v in zip(messages, vectors)
    ]
    await get_qdrant().upsert(collection_name=user_collection(user_id), points=points)
    return len(points)


async def retrieve_similar(user_id: int, query: str, top_k: int = 12) -> list[dict[str, Any]]:
    await ensure_user_collection(user_id)
    qvec = await embed(_Q + query)
    res = await get_qdrant().query_points(
        collection_name=user_collection(user_id), query=qvec, limit=top_k, with_payload=True
    )
    return [
        {"text": (p.payload or {}).get("text", ""), "score": p.score, **(p.payload or {})}
        for p in res.points
    ]
