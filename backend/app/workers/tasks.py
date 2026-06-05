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
    import httpx

    from app.core.config import settings
    from app.db.mongo import get_mongo
    from app.services.style_memory import add_messages

    async def _go():
        async with httpx.AsyncClient(base_url=settings.WHATSAPP_BRIDGE_URL, timeout=120.0) as cli:
            r = await cli.get(
                f"/sessions/{user_id}/history",
                params={"contact_id": contact_wa_id, "limit": limit},
            )
            r.raise_for_status()
            history = r.json().get("messages", [])
        if not history:
            return {"saved": 0}

        mongo = get_mongo()
        docs = []
        for m in history:
            docs.append(
                {
                    "user_id": user_id,
                    "wa_id": m.get("from"),
                    "contact_id": None,  # backfilled when contact resolved
                    "direction": m.get("direction", "in"),
                    "text": m.get("text"),
                    "ts": m.get("ts"),
                    "meta": m.get("meta", {}),
                }
            )
        await mongo.messages.insert_many(docs)

        # Only embed user-authored ("out") messages for style learning
        own = [d for d in docs if d.get("direction") == "out" and d.get("text")]
        added = await add_messages(
            user_id,
            [{"id": str(uuid.uuid4()), "text": d["text"], "ts": d.get("ts"), "wa_id": d.get("wa_id"), "direction": "out"} for d in own],
        )
        return {"saved": len(docs), "embedded": added}

    return _run(_go())


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
    from app.services.style_memory import retrieve_similar
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

        similar = await retrieve_similar(user_id=user_id, query=text, top_k=12)
        prompt = build_runtime_prompt(
            similar_history=[s["text"] for s in similar],
            recent_turns=[],
            incoming_message=text,
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
