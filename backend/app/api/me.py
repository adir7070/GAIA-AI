"""User self-service: export all data, delete all data (privacy spec §29)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.db.models.contact import Contact
from app.db.models.feedback import Feedback
from app.db.models.permission import Permission
from app.db.models.session import Session as SessionModel
from app.db.models.user import User
from app.db.mongo import get_mongo
from app.db.qdrant import get_qdrant, user_collection

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/export")
async def export_data(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
    contacts = (
        await db.execute(select(Contact).where(Contact.user_id == user_id))
    ).scalars().all()
    permissions = (
        await db.execute(select(Permission).where(Permission.user_id == user_id))
    ).scalars().all()
    feedback = (
        await db.execute(select(Feedback).where(Feedback.user_id == user_id))
    ).scalars().all()

    mongo = get_mongo()
    messages = [d async for d in mongo.messages.find({"user_id": user_id})]
    ai_outputs = [d async for d in mongo.ai_outputs.find({"user_id": user_id})]

    payload = {
        "exported_at": datetime.now(tz=timezone.utc).isoformat(),
        "user": {"id": user.id, "email": user.email, "display_name": user.display_name},
        "contacts": [
            {"id": c.id, "wa_id": c.wa_id, "name": c.name, "is_group": c.is_group, "allowed": c.allowed}
            for c in contacts
        ],
        "permissions": [
            {"id": p.id, "contact_id": p.contact_id, "suggest": p.suggest, "auto_send": p.auto_send}
            for p in permissions
        ],
        "feedback": [
            {
                "id": f.id,
                "suggestion_id": f.suggestion_id,
                "incoming_message": f.incoming_message,
                "original": f.original,
                "edited": f.edited,
                "decision": f.decision,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedback
        ],
        "messages": [_strip_id(m) for m in messages],
        "ai_outputs": [_strip_id(m) for m in ai_outputs],
    }
    return Response(
        content=json.dumps(payload, ensure_ascii=False, default=str, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="gaia-export-user-{user_id}.json"'},
    )


@router.delete("/data")
async def delete_all(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Hard delete all user data across Postgres, Mongo, Qdrant. Account row remains - call DELETE /me to remove the user."""
    await db.execute(delete(Feedback).where(Feedback.user_id == user_id))
    await db.execute(delete(Permission).where(Permission.user_id == user_id))
    await db.execute(delete(Contact).where(Contact.user_id == user_id))
    await db.execute(delete(SessionModel).where(SessionModel.user_id == user_id))
    await db.commit()

    mongo = get_mongo()
    await mongo.messages.delete_many({"user_id": user_id})
    await mongo.ai_outputs.delete_many({"user_id": user_id})
    await mongo.training_samples.delete_many({"user_id": user_id})

    try:
        await get_qdrant().delete_collection(user_collection(user_id))
    except Exception:
        pass

    return {"ok": True}


@router.delete("")
async def delete_account(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete the user account itself (cascades to all related rows via FK)."""
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    mongo = get_mongo()
    await mongo.messages.delete_many({"user_id": user_id})
    await mongo.ai_outputs.delete_many({"user_id": user_id})
    await mongo.training_samples.delete_many({"user_id": user_id})

    try:
        await get_qdrant().delete_collection(user_collection(user_id))
    except Exception:
        pass

    return {"ok": True}


def _strip_id(d: dict) -> dict:
    d = dict(d)
    d.pop("_id", None)
    return d
