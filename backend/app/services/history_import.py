"""Import a single contact's chat history from the bridge into Mongo + Qdrant.

Shared by the Celery task (gaia.import_history) and the on-demand profile resync,
so both behave identically.
"""
from __future__ import annotations

import logging
import uuid

import httpx

from app.core.config import settings
from app.db.mongo import get_mongo
from app.services.style_memory import add_messages

log = logging.getLogger(__name__)


async def import_contact_history(user_id: int, contact_wa_id: str, limit: int = 200) -> dict:
    """Pull last N messages for a contact, store in Mongo, embed the user's own
    ('out') messages into the style collection. Returns counts."""
    try:
        async with httpx.AsyncClient(base_url=settings.WHATSAPP_BRIDGE_URL, timeout=120.0) as cli:
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

    own = [d for d in docs if d.get("direction") == "out" and d.get("text")]
    embedded = await add_messages(
        user_id,
        [
            {"id": str(uuid.uuid4()), "text": d["text"], "ts": d.get("ts"), "wa_id": d.get("wa_id"), "direction": "out"}
            for d in own
        ],
    )
    return {"saved": len(docs), "embedded": embedded}
