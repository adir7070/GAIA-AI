"""Import a single contact's chat history from the bridge into Mongo + Qdrant.

Shared by the Celery task (gaia.import_history) and the on-demand profile resync,
so both behave identically.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.db.mongo import get_mongo
from app.services.style_memory import add_pairs

log = logging.getLogger(__name__)


_MAX_REPLY_GAP_MS = 30 * 60 * 1000  # 30 minutes — beyond this it's a new topic, not a reply


def _build_pairs(history: list[dict]) -> list[dict]:
    """Build genuine (their message → your reply) pairs from a chat history.

    Only pairs messages that are temporally close (≤30 min gap) to avoid
    false pairs where the user's reply is actually about a completely different
    topic from an earlier part of the conversation.
    """
    msgs = sorted(history, key=lambda m: m.get("ts") or 0)
    pairs: list[dict] = []
    last_in: str | None = None
    last_in_ts: int | None = None

    for m in msgs:
        txt = (m.get("text") or "").strip()
        if not txt:
            continue
        ts = m.get("ts") or 0

        if m.get("direction") == "in":
            last_in = txt[:400]
            last_in_ts = ts
        elif m.get("direction") == "out" and last_in:
            # Drop pair if too much time passed — they're not a real exchange
            gap = ts - (last_in_ts or 0)
            if gap <= _MAX_REPLY_GAP_MS:
                pairs.append({"incoming": last_in, "reply": txt[:400], "ts": ts})
            last_in = None
            last_in_ts = None

    return pairs


async def import_contact_history(user_id: int, contact_wa_id: str, limit: int = 3000) -> dict:
    """Pull last N messages for a contact, store in Mongo, embed the user's own
    ('out') messages into the style collection. Returns counts."""
    try:
        async with httpx.AsyncClient(base_url=settings.WHATSAPP_BRIDGE_URL, timeout=300.0) as cli:
            r = await cli.get(
                f"/sessions/{user_id}/history",
                params={"contact_id": contact_wa_id, "limit": limit},
            )
            r.raise_for_status()
            history = r.json().get("messages", [])
    except Exception as e:  # noqa: BLE001 - chat may not exist / bridge busy
        log.warning("history import failed for %s/%s: %s", user_id, contact_wa_id, e)
        return {"saved": 0, "embedded": 0}

    if not history:
        return {"saved": 0, "embedded": 0}

    docs = [
        {
            "user_id": user_id,
            "wa_id": m.get("from"),
            "chat_wa_id": contact_wa_id,
            "contact_id": None,
            "direction": m.get("direction", "in"),
            "text": m.get("text"),
            "ts": m.get("ts"),
            "meta": m.get("meta", {}),
        }
        for m in history
    ]
    await get_mongo().messages.insert_many(docs)

    # Build & embed (their message -> your reply) pairs — the basis for 1:1 cloning.
    pairs = _build_pairs(history)
    embedded = await add_pairs(user_id, pairs)
    return {"saved": len(docs), "pairs": embedded}
