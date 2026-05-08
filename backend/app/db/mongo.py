"""Motor async MongoDB client."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo() -> AsyncIOMotorDatabase:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI, tz_aware=True)
    return _client[settings.MONGO_DB]


async def ensure_mongo_indexes() -> None:
    db = get_mongo()
    await db.messages.create_index([("user_id", 1), ("contact_id", 1), ("ts", -1)])
    await db.messages.create_index([("user_id", 1), ("ts", -1)])
    await db.training_samples.create_index([("user_id", 1)])
    await db.ai_outputs.create_index([("user_id", 1), ("created_at", -1)])
