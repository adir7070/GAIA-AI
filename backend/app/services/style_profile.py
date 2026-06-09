"""User Style Profile: make the implicit learned style EXPLICIT, rich, editable,
and feed it back into generation.

- analyze_style: read the user's OWN ("out") messages (as many as fit a char
  budget), ask the LLM to extract a detailed structured profile, store it.
- get_profile / save_profile: read + upsert (the user can edit everything).
- The business section is preserved across re-analysis once the user fills it in.
- The profile is injected into the runtime prompt (see prompt_builder), so edits
  change the model's responses.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.db.mongo import get_mongo
from app.prompts.style_analysis import STYLE_ANALYSIS_PROMPT
from app.services.llm_provider import generate_text

log = logging.getLogger(__name__)

# Character budget for the messages we feed the analyzer. Free Groq tiers cap
# tokens-per-MINUTE (~12k for 70B), and a single request must fit under that —
# so we sample a REPRESENTATIVE set spread across the whole history rather than
# dumping everything. The sampling is evenly distributed so even with 3000
# messages, the analyzer sees a broad cross-section of the user's style.
# Hebrew tokenizes at ~1 token/char; keep total input under ~8k to leave room
# for the output and avoid rate-limit errors.
CHAR_BUDGET = 8000
PER_MSG_CAP = 300


def _extract_json(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if "\n" in t:
            t = t.split("\n", 1)[1]
    start, end = t.find("{"), t.rfind("}")
    return t[start : end + 1] if start != -1 and end != -1 else t


async def get_profile(user_id: int) -> dict | None:
    doc = await get_mongo().style_profiles.find_one({"user_id": user_id})
    if doc:
        doc.pop("_id", None)
    return doc


async def count_out_messages(user_id: int) -> int:
    return await get_mongo().messages.count_documents({"user_id": user_id, "direction": "out"})


async def save_profile(
    user_id: int,
    summary: str,
    traits: dict,
    *,
    business: dict | None = None,
    edited: bool,
    analyzed_count: int | None = None,
) -> dict:
    doc: dict = {
        "user_id": user_id,
        "summary": summary,
        "traits": traits or {},
        "business": business or {},
        "edited": edited,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if analyzed_count is not None:
        doc["analyzed_count"] = analyzed_count
    await get_mongo().style_profiles.update_one(
        {"user_id": user_id}, {"$set": doc}, upsert=True
    )
    return doc


async def _collect_messages(user_id: int) -> list[str]:
    """A representative sample of the user's own messages spread across ALL their
    history, trimmed to fit the per-request token budget."""
    cursor = get_mongo().messages.find(
        {"user_id": user_id, "direction": "out", "text": {"$ne": None}}
    )
    texts: list[str] = []
    async for d in cursor:
        t = (d.get("text") or "").strip()
        if t:
            texts.append(t[:PER_MSG_CAP])
    if not texts:
        return []

    total = sum(len(t) for t in texts)
    if total <= CHAR_BUDGET:
        return texts

    # Evenly sample across the whole history so the profile reflects all of it.
    avg = max(1, total // len(texts))
    target = max(1, CHAR_BUDGET // avg)
    stride = max(1, len(texts) // target)
    sampled = texts[::stride]
    # final trim to budget
    out: list[str] = []
    acc = 0
    for t in sampled:
        if acc + len(t) > CHAR_BUDGET:
            break
        out.append(t)
        acc += len(t)
    return out


MAX_RESYNC_CONTACTS = 15
RESYNC_MSGS_PER_CONTACT = 3000


async def resync_and_analyze(user_id: int) -> dict:
    """Re-import ONLY the user's currently-allowed (selected) chats from scratch,
    then analyze the profile from those messages alone — for an accurate profile.

    Raises ValueError('no_selection') if no contacts are allowed.
    """
    from sqlalchemy import select

    from app.db.models.contact import Contact
    from app.db.postgres import async_session_maker
    from app.services.history_import import import_contact_history
    from app.services.style_memory import reset_pairs_collection

    async with async_session_maker() as db:
        allowed = (
            await db.execute(
                select(Contact.wa_id).where(Contact.user_id == user_id, Contact.allowed.is_(True))
            )
        ).scalars().all()

    if not allowed:
        raise ValueError("no_selection")

    chosen = list(allowed)[:MAX_RESYNC_CONTACTS]

    # Start from zero: wipe previously-imported messages + embedded pairs.
    await get_mongo().messages.delete_many({"user_id": user_id})
    await reset_pairs_collection(user_id)

    imported = 0
    for wa in chosen:
        res = await import_contact_history(user_id, wa, RESYNC_MSGS_PER_CONTACT)
        imported += res.get("saved", 0)
    log.info("resync user %s: %d chats, %d messages", user_id, len(chosen), imported)

    return await analyze_style(user_id)


async def analyze_style(user_id: int) -> dict:
    """Analyze the user's own messages into a fresh, rich profile.

    Raises ValueError('no_messages') or ValueError('parse_failed').
    Preserves an existing user-edited business section.
    """
    msgs = await _collect_messages(user_id)
    if not msgs:
        raise ValueError("no_messages")

    sample = "\n".join(f"- {m}" for m in msgs)
    raw = await generate_text(
        STYLE_ANALYSIS_PROMPT.format(messages=sample),
        system="Return only valid JSON. Be concrete and specific. Never write 'כפי שנראה בהודעות'.",
        max_tokens=2048,
        temperature=0.4,
    )
    try:
        data = json.loads(_extract_json(raw))
    except Exception as e:  # noqa: BLE001
        log.warning("style analysis parse failed for user %s: %s", user_id, e)
        raise ValueError("parse_failed") from e

    # Preserve a business section the user already filled in.
    existing = await get_profile(user_id)
    existing_biz = (existing or {}).get("business") or {}
    inferred_biz = data.get("business") or {}
    business = existing_biz if existing_biz.get("name") or existing_biz.get("description") else inferred_biz

    return await save_profile(
        user_id,
        data.get("summary", ""),
        data.get("traits", {}),
        business=business,
        edited=False,
        analyzed_count=len(msgs),
    )
