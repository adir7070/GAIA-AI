"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai as ai_routes
from app.api import analytics as analytics_routes
from app.api import auth as auth_routes
from app.api import contacts as contacts_routes
from app.api import me as me_routes
from app.api import messages as messages_routes
from app.api import profile as profile_routes
from app.api import whatsapp as whatsapp_routes
from app.api import ws as ws_routes
from app.core.config import settings
from app.db.mongo import ensure_mongo_indexes
from app.db.postgres import init_db

logging.basicConfig(level=settings.LOG_LEVEL)
log = logging.getLogger("gaia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting Gaia AI backend (env=%s)", settings.ENV)
    try:
        await init_db()
    except Exception as e:
        log.warning("init_db failed (will rely on alembic migrations): %s", e)
    try:
        await ensure_mongo_indexes()
    except Exception as e:
        log.warning("mongo index init failed: %s", e)
    yield


app = FastAPI(
    title="Gaia AI",
    version="0.1.0",
    description="Personalized response generation via implicit user-style learning.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_routes.router)
app.include_router(whatsapp_routes.router)
app.include_router(contacts_routes.router)
app.include_router(messages_routes.router)
app.include_router(ai_routes.router)
app.include_router(analytics_routes.router)
app.include_router(me_routes.router)
app.include_router(profile_routes.router)
app.include_router(ws_routes.router)
