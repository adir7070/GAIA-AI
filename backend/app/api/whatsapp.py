"""WhatsApp endpoints. Backend proxies to the Node bridge service."""
from __future__ import annotations

import json

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user_id, get_db
from app.core.security import hmac_verify
from app.db.models.contact import Contact
from app.db.models.session import Session as SessionModel
from app.db.mongo import get_mongo
from app.db.qdrant import ensure_user_collection
from app.schemas.whatsapp import ConnectResponse, QrResponse, SendRequest, WebhookEvent

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def _bridge() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=settings.WHATSAPP_BRIDGE_URL, timeout=20.0)


@router.post("/connect", response_model=ConnectResponse)
async def connect(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ConnectResponse:
    """Start a WhatsApp Web session for the current user."""
    async with _bridge() as cli:
        r = await cli.post("/sessions", json={"user_id": user_id})
        r.raise_for_status()
        data = r.json()

    sess = SessionModel(
        user_id=user_id,
        wa_session_id=data.get("session_id", str(user_id)),
        status=data.get("status", "pending"),
    )
    db.add(sess)
    await db.commit()
    await ensure_user_collection(user_id)
    return ConnectResponse(session_id=sess.wa_session_id, status=sess.status)


@router.get("/qr", response_model=QrResponse)
async def get_qr(user_id: int = Depends(get_current_user_id)) -> QrResponse:
    async with _bridge() as cli:
        r = await cli.get(f"/sessions/{user_id}/qr")
        if r.status_code == 404:
            return QrResponse(status="pending")
        r.raise_for_status()
        d = r.json()
    return QrResponse(qr_base64=d.get("qr_base64"), status=d.get("status", "pending"))


@router.post("/send")
async def send_message(
    body: SendRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    contact = (
        await db.execute(
            select(Contact).where(Contact.id == body.contact_id, Contact.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not contact:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "contact not found")

    async with _bridge() as cli:
        r = await cli.post(
            f"/sessions/{user_id}/send",
            json={"to": contact.wa_id, "text": body.text},
        )
        r.raise_for_status()
    return {"ok": True}


@router.delete("/disconnect")
async def disconnect(user_id: int = Depends(get_current_user_id)):
    async with _bridge() as cli:
        await cli.delete(f"/sessions/{user_id}")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Internal webhook called by the WhatsApp bridge (HMAC-protected).
# ---------------------------------------------------------------------------
@router.post("/internal/event", include_in_schema=False)
async def bridge_webhook(
    request: Request,
    x_bridge_signature: str = Header(default=""),
):
    body = await request.body()
    if not hmac_verify(body, x_bridge_signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad signature")

    event = WebhookEvent(**json.loads(body))

    if event.type == "message":
        from app.workers.tasks import handle_incoming_message  # local import to avoid cycle

        # Persist + dispatch async generation.
        msg = event.payload
        mongo = get_mongo()
        await mongo.messages.insert_one(
            {
                "user_id": event.user_id,
                "wa_id": msg.get("from"),
                "direction": msg.get("direction", "in"),
                "text_encrypted": msg.get("text_encrypted") or msg.get("text"),
                "ts": msg.get("ts"),
                "meta": msg.get("meta", {}),
            }
        )
        handle_incoming_message.delay(event.user_id, msg)

    return {"ok": True}
