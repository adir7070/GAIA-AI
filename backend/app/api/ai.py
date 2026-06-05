"""AI suggestion + feedback endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.db.models.contact import Contact
from app.db.models.feedback import Feedback
from app.db.mongo import get_mongo
from app.schemas.ai import FeedbackRequest, FeedbackResponse, GenerateRequest, GenerateResponse
from app.services.confidence import score_confidence
from app.services.prompt_builder import build_runtime_prompt
from app.services.style_memory import retrieve_similar
from app.services.llm_provider import generate_text

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    contact = (
        await db.execute(
            select(Contact).where(Contact.id == body.contact_id, Contact.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not contact:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "contact not found")
    if not contact.allowed:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "AI suggestions are not enabled for this contact"
        )

    similar = await retrieve_similar(user_id=user_id, query=body.incoming_message, top_k=12)
    recent = await _recent_turns(user_id, contact.id, n=8)

    from app.services.style_profile import get_profile

    prompt = build_runtime_prompt(
        similar_history=[s["text"] for s in similar],
        recent_turns=recent,
        incoming_message=body.incoming_message,
        style_profile=await get_profile(user_id),
    )
    suggestion = await generate_text(prompt, max_tokens=512, temperature=0.6)
    confidence, label = score_confidence(suggestion=suggestion, similar=similar)

    suggestion_id = str(uuid.uuid4())
    await get_mongo().ai_outputs.insert_one(
        {
            "user_id": user_id,
            "suggestion_id": suggestion_id,
            "contact_id": contact.id,
            "incoming": body.incoming_message,
            "suggestion": suggestion,
            "confidence": confidence,
            "label": label,
            "created_at": datetime.now(tz=timezone.utc),
        }
    )

    return GenerateResponse(
        suggestion_id=suggestion_id,
        suggestion=suggestion,
        confidence=confidence,
        label=label,
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(
    body: FeedbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    out = await get_mongo().ai_outputs.find_one(
        {"user_id": user_id, "suggestion_id": body.suggestion_id}
    )
    if not out:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "suggestion not found")
    fb = Feedback(
        user_id=user_id,
        suggestion_id=body.suggestion_id,
        contact_id=out.get("contact_id"),
        incoming_message=out.get("incoming", ""),
        original=out.get("suggestion", ""),
        edited=body.edited_text,
        delta_json={"len_orig": len(out.get("suggestion", "")), "len_edit": len(body.edited_text)},
        decision=body.decision,
    )
    db.add(fb)
    await db.commit()
    return FeedbackResponse(ok=True)


async def _recent_turns(user_id: int, contact_id: int, n: int) -> list[dict]:
    cursor = (
        get_mongo()
        .messages.find({"user_id": user_id, "contact_id": contact_id})
        .sort("ts", -1)
        .limit(n)
    )
    out = [doc async for doc in cursor]
    return list(reversed(out))
