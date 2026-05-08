from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_id
from app.core.security import decrypt_text
from app.db.mongo import get_mongo

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("")
async def list_messages(
    contact_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    before: datetime | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
):
    q: dict[str, Any] = {"user_id": user_id}
    if contact_id is not None:
        q["contact_id"] = contact_id
    if before is not None:
        q["ts"] = {"$lt": before}
    cursor = get_mongo().messages.find(q).sort("ts", -1).limit(limit)
    out = []
    async for d in cursor:
        text = d.get("text") or ""
        if not text and d.get("text_encrypted"):
            try:
                text = decrypt_text(d["text_encrypted"])
            except Exception:
                text = "[encrypted]"
        out.append(
            {
                "id": str(d.get("_id")),
                "contact_id": d.get("contact_id"),
                "wa_id": d.get("wa_id"),
                "direction": d.get("direction"),
                "text": text,
                "ts": d.get("ts"),
            }
        )
    return out
