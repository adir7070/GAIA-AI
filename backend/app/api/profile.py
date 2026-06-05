"""Style Profile endpoints — view, (re)analyze, and edit how the model sees the user."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import get_current_user_id
from app.services.style_profile import (
    analyze_style,
    count_out_messages,
    get_profile,
    save_profile,
)

router = APIRouter(prefix="/style-profile", tags=["style-profile"])


class ProfileIn(BaseModel):
    summary: str
    traits: dict


@router.get("")
async def read_profile(user_id: int = Depends(get_current_user_id)):
    return {
        "profile": await get_profile(user_id),
        "message_count": await count_out_messages(user_id),
    }


@router.post("/analyze")
async def analyze(user_id: int = Depends(get_current_user_id)):
    try:
        profile = await analyze_style(user_id)
    except ValueError as e:
        if str(e) == "no_messages":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "אין מספיק הודעות שלך לניתוח. אשר אנשי קשר בעמוד ההרשאות כדי לייבא היסטוריה, ואז נתח שוב.",
            )
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "ניתוח הסגנון נכשל, נסה שוב.")
    return {"profile": profile}


@router.put("")
async def update_profile(body: ProfileIn, user_id: int = Depends(get_current_user_id)):
    profile = await save_profile(user_id, body.summary, body.traits, edited=True)
    return {"profile": profile}
