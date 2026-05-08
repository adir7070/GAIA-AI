"""Async SQLAlchemy engine + session factory + Base."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Best-effort table creation on startup (Alembic owns the real schema)."""
    from app.db.models import all_models  # noqa: F401  - register mappers

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
