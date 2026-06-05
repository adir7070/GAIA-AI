"""User Style Profile: make the implicit learned style EXPLICIT, editable, and
feed it back into generation.

- analyze_style: read the user's own ("out") messages, ask the LLM to extract a
  structured profile, store it in Mongo.
- get_profile / save_profile: read + upsert (the user can edit it).
- The profile is injected into the runtime prompt (see prompt_builder), so when
  the user edits it, the model's responses change accordingly.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.db.mongo import get_mongo
from app.prompts.style_analysis import STYLE_ANALYSIS_PROMPT
from app.services.llm_provider import generate_text

log = logging.getLogger(__name__)

SAMPLE_SIZE = 80


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


async def save_profile(user_id: int, summary: str, traits: dict, *, edited: bool) -> dict:
    doc = {
        "user_id": user_id,
        "summary": summary,
        "traits": traits or {},
        "edited": edited,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    await get_mongo().style_profiles.update_one(
        {"user_id": user_id}, {"$set": doc}, upsert=True
    )
    return doc


async def analyze_style(user_id: int) -> dict:
    """Analyze the user's own messages into a fresh profile. Raises ValueError('no_messages')."""
    mongo = get_mongo()
    cursor = (
        mongo.messages.find({"user_id": user_id, "direction": "out", "text": {"$ne": None}})
        .sort("ts", -1)
        .limit(SAMPLE_SIZE)
    )
    msgs = [d["text"] async for d in cursor if d.get("text")]
    if not msgs:
        raise ValueError("no_messages")

    sample = "\n".join(f"- {m}" for m in msgs)
    raw = await generate_text(
        STYLE_ANALYSIS_PROMPT.format(messages=sample),
        system="Return only valid JSON.",
        max_tokens=900,
        temperature=0.4,
    )
    try:
        data = json.loads(_extract_json(raw))
    except Exception as e:  # noqa: BLE001
        log.warning("style analysis parse failed for user %s: %s", user_id, e)
        raise ValueError("parse_failed") from e

    return await save_profile(
        user_id, data.get("summary", ""), data.get("traits", {}), edited=False
    )
