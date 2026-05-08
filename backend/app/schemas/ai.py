from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    contact_id: int
    incoming_message: str = Field(min_length=1, max_length=4096)


class GenerateResponse(BaseModel):
    suggestion_id: str
    suggestion: str
    confidence: float
    label: Literal["ANSWER_NOW", "ASK_USER_FOR_TEACHING", "UNSURE"]
    explanation: str | None = None


class FeedbackRequest(BaseModel):
    suggestion_id: str
    edited_text: str
    decision: Literal["approve", "edit", "skip"] = "edit"


class FeedbackResponse(BaseModel):
    ok: bool = True
