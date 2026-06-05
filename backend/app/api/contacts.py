from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.db.models.contact import Contact
from app.schemas.contact import ContactOut, ContactPatch
from app.services.contacts_sync import sync_user_contacts

router = APIRouter(prefix="/contacts", tags=["contacts"])


async def _list(db: AsyncSession, user_id: int) -> list[ContactOut]:
    rows = (
        await db.execute(select(Contact).where(Contact.user_id == user_id).order_by(Contact.name))
    ).scalars().all()
    return [
        ContactOut(id=c.id, wa_id=c.wa_id, name=c.name, is_group=c.is_group, allowed=c.allowed)
        for c in rows
    ]


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    return await _list(db, user_id)


@router.post("/sync", response_model=list[ContactOut])
async def sync_contacts(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    """Pull the user's WhatsApp contacts from the bridge into Postgres, then return them."""
    await sync_user_contacts(user_id)
    return await _list(db, user_id)


@router.patch("/{contact_id}", response_model=ContactOut)
async def patch_contact(
    contact_id: int,
    body: ContactPatch,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    c = (
        await db.execute(
            select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "contact not found")
    newly_allowed = body.allowed is True and not c.allowed
    if body.allowed is not None:
        c.allowed = body.allowed
    if body.name is not None:
        c.name = body.name
    await db.commit()
    await db.refresh(c)

    # When a contact is first allowed, import their history so the model can
    # learn the user's style with that person (style memory in Qdrant).
    if newly_allowed:
        try:
            from app.workers.tasks import import_history

            import_history.delay(user_id, c.wa_id)
        except Exception:  # noqa: BLE001 - worker/broker hiccup shouldn't fail the toggle
            pass

    return ContactOut(id=c.id, wa_id=c.wa_id, name=c.name, is_group=c.is_group, allowed=c.allowed)
