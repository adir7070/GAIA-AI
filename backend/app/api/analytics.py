from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.db.models.feedback import Feedback
from app.db.mongo import get_mongo

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    since = datetime.now(tz=timezone.utc) - timedelta(days=30)
    suggestions_count = await get_mongo().ai_outputs.count_documents(
        {"user_id": user_id, "created_at": {"$gte": since}}
    )
    fb_count = (
        await db.execute(
            select(func.count(Feedback.id)).where(
                Feedback.user_id == user_id, Feedback.created_at >= since
            )
        )
    ).scalar_one()
    approve = (
        await db.execute(
            select(func.count(Feedback.id)).where(
                Feedback.user_id == user_id,
                Feedback.created_at >= since,
                Feedback.decision == "approve",
            )
        )
    ).scalar_one()
    edit = (
        await db.execute(
            select(func.count(Feedback.id)).where(
                Feedback.user_id == user_id,
                Feedback.created_at >= since,
                Feedback.decision == "edit",
            )
        )
    ).scalar_one()
    return {
        "window_days": 30,
        "suggestions": suggestions_count,
        "feedback": fb_count,
        "approved": approve,
        "edited": edit,
        "approval_rate": (approve / fb_count) if fb_count else None,
    }
