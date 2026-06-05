"""Celery tasks. Each task is a thin sync wrapper that drives async coroutines."""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if asyncio.get_event_loop().is_running() is False else asyncio.run(coro)


# ----- Embed messages into Qdrant -----------------------------------------
@celery_app.task(name="gaia.embed_messages")
def embed_messages(user_id: int, messages: list[dict]) -> int:
    from app.services.style_memory import add_messages

    return _run(add_messages(user_id, messages))


# ----- Initial history sync ------------------------------------------------
@celery_app.task(name="gaia.import_history")
def import_history(user_id: int, contact_wa_id: str, limit: int = 1000) -> dict:
    """Pull last N messages for a contact from the bridge, store in Mongo + Qdrant."""
    from app.services.history_import import import_contact_history

    return _run(import_contact_history(user_id, contact_wa_id, limit))


# ----- Generate suggestion (called from webhook) ---------------------------
@celery_app.task(name="gaia.handle_incoming_message")
def handle_incoming_message(user_id: int, message: dict) -> None:
    """Triggered by /whatsapp/internal/event for an incoming message.
    Generates a suggestion and pushes it to the user via WS.
    """
    from app.api.ws import push_to_user
    from app.db.mongo import get_mongo
    from app.services.confidence import score_confidence
    from app.services.llm_provider import generate_text
    from app.services.prompt_builder import build_runtime_prompt
    from app.services.style_memory import retrieve_pairs
    from sqlalchemy import select

    from app.db.models.contact import Contact
    from app.db.postgres import async_session_maker

    async def _go():
        wa_id = message.get("from") or message.get("wa_id")
        text = message.get("text") or ""
        if not wa_id or not text:
            return

        async with async_session_maker() as db:
            contact = (
                await db.execute(
                    select(Contact).where(Contact.user_id == user_id, Contact.wa_id == wa_id)
                )
            ).scalar_one_or_none()

        if not contact:
            log.info("incoming from unknown contact %s for user %s; skipping", wa_id, user_id)
            return
        if not contact.allowed:
            return

        from app.services.style_profile import get_profile

        examples = await retrieve_pairs(user_id=user_id, query=text, top_k=8)
        prompt = build_runtime_prompt(
            examples=examples,
            incoming_message=text,
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
                "wa_id": wa_id,
                "incoming": text,
                "suggestion": suggestion,
                "confidence": confidence,
                "label": label,
                "created_at": datetime.now(tz=timezone.utc),
            }
        )

        await push_to_user(
            user_id,
            {
                "event": "new_suggestion",
                "data": {
                    "suggestion_id": suggestion_id,
                    "contact_id": contact.id,
                    "contact_name": contact.name or contact.wa_id,
                    "incoming": text,
                    "suggestion": suggestion,
                    "confidence": confidence,
                    "label": label,
                },
            },
        )

    _run(_go())
