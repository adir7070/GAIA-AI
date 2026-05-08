from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.db.models.contact import Contact
from app.schemas.contact import ContactOut, ContactPatch

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(select(Contact).where(Contact.user_id == user_id).order_by(Contact.name))
    ).scalars().all()
    return [
        ContactOut(
            id=c.id, wa_id=c.wa_id, name=c.name, is_group=c.is_group, allowed=c.allowed
        )
        for c in rows
    ]


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
    if body.allowed is not None:
        c.allowed = body.allowed
    if body.name is not None:
        c.name = body.name
    await db.commit()
    await db.refresh(c)
    return ContactOut(id=c.id, wa_id=c.wa_id, name=c.name, is_group=c.is_group, allowed=c.allowed)
