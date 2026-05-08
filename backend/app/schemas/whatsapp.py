from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class QrResponse(BaseModel):
    qr_base64: str | None = None
    status: Literal["pending", "ready", "error", "disconnected"] = "pending"


class ConnectResponse(BaseModel):
    session_id: str
    status: str


class SendRequest(BaseModel):
    contact_id: int
    text: str


class WebhookEvent(BaseModel):
    user_id: int
    type: Literal["message", "ready", "qr", "disconnected"]
    payload: dict
