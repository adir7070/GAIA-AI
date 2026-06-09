"""AI suggestion + feedback endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.db.models.contact import Contact
from app.db.models.feedback import Feedback
from app.db.mongo import get_mongo
from app.schemas.ai import FeedbackRequest, FeedbackResponse, GenerateRequest, GenerateResponse
from app.services.confidence import score_confidence
from app.services.prompt_builder import build_runtime_prompt, build_system_message
from app.services.style_memory import retrieve_pairs
from app.services.llm_provider import generate_text, generate_with_history

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

    from app.services.style_profile import get_profile

    examples = await retrieve_pairs(user_id, body.incoming_message, top_k=8)
    prompt = build_runtime_prompt(
        examples=examples,
        incoming_message=body.incoming_message,
        style_profile=await get_profile(user_id),
    )
    suggestion = await generate_text(prompt, max_tokens=400, temperature=0.6)
    confidence, label = score_confidence(suggestion=suggestion, similar=examples)

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


class ConversationTurn(BaseModel):
    role: Literal["them", "me"]
    text: str


class TestRequest(BaseModel):
    incoming_message: str
    conversation_history: list[ConversationTurn] = []


@router.post("/test")
async def test_generate(
    body: TestRequest, user_id: int = Depends(get_current_user_id)
) -> dict:
    """Playground: generate a reply in the user's style for any message, no contact
    needed. Supports multi-turn conversation history for coherent dialogue."""
    from app.services.style_profile import get_profile

    style_profile = await get_profile(user_id)
    system = build_system_message(style_profile)
    examples = await retrieve_pairs(user_id, body.incoming_message, top_k=6)

    # Convert playground turns to LLM-native user/assistant format.
    # "them" = the other person = user role; "me" = the clone = assistant role.
    history: list[dict] = [
        {"role": "user" if t.role == "them" else "assistant", "content": t.text}
        for t in body.conversation_history
    ]
    history.append({"role": "user", "content": body.incoming_message})

    suggestion = await generate_with_history(system=system, history=history)
    sources = [
        {
            "incoming": e.get("incoming", ""),
            "reply": e.get("reply", ""),
            "score": round(float(e.get("score", 0)), 3),
        }
        for e in examples[:6]
    ]
    return {"suggestion": suggestion, "used_history": len(examples), "sources": sources}


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


@router.get("/suggestions")
async def list_suggestions(
    limit: int = Query(default=20, le=100),
    user_id: int = Depends(get_current_user_id),
) -> list[dict]:
    """Return the most recent AI suggestions for the dashboard history."""
    cursor = (
        get_mongo()
        .ai_outputs.find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    out = []
    async for doc in cursor:
        doc.pop("_id", None)
        out.append(doc)
    return out


async def _recent_turns(user_id: int, contact_id: int, n: int) -> list[dict]:
    cursor = (
        get_mongo()
        .messages.find({"user_id": user_id, "contact_id": contact_id})
        .sort("ts", -1)
        .limit(n)
    )
    out = [doc async for doc in cursor]
    return list(reversed(out))
