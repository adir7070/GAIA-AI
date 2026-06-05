"""Sync a user's WhatsApp contacts from the bridge into Postgres.

This is the integration step that lets the /permissions page show the user's
contacts so they can opt specific people in. New contacts are inserted with
allowed=False (explicit per-contact opt-in); existing ones keep their flag and
only get their display name refreshed.
"""
from __future__ import annotations

import logging

import httpx
from sqlalchemy import select

from app.core.config import settings
from app.db.models.contact import Contact
from app.db.postgres import async_session_maker

log = logging.getLogger(__name__)


async def sync_user_contacts(user_id: int) -> int:
    """Pull contacts from the bridge and upsert them. Returns the number seen."""
    try:
        async with httpx.AsyncClient(base_url=settings.WHATSAPP_BRIDGE_URL, timeout=60.0) as cli:
            r = await cli.get(f"/sessions/{user_id}/contacts")
            r.raise_for_status()
            contacts = r.json().get("contacts", [])
    except Exception as e:  # noqa: BLE001 - bridge not ready / no session
        log.warning("contact sync failed for user %s: %s", user_id, e)
        return 0

    if not contacts:
        return 0

    async with async_session_maker() as db:
        existing = {
            c.wa_id: c
            for c in (
                await db.execute(select(Contact).where(Contact.user_id == user_id))
            ).scalars().all()
        }
        for c in contacts:
            wa_id = c.get("wa_id")
            name = c.get("name")
            is_group = bool(c.get("is_group"))
            # Only sync the real address book — named contacts and groups.
            # WhatsApp returns thousands of unsaved bare numbers; skip those so
            # the permissions list stays usable.
            if not wa_id or (not name and not is_group):
                continue
            row = existing.get(wa_id)
            if row:
                # Already in DB or seen earlier in THIS batch (the bridge list
                # contains duplicate wa_ids) — update instead of re-inserting.
                if name and row.name != name:
                    row.name = name
                row.is_group = is_group
            else:
                row = Contact(
                    user_id=user_id,
                    wa_id=wa_id,
                    name=name,
                    is_group=is_group,
                    allowed=False,
                )
                db.add(row)
                existing[wa_id] = row  # guard against same wa_id appearing again
        await db.commit()
        total = len(existing)
    log.info("synced contacts for user %s (%d total)", user_id, total)
    return total
