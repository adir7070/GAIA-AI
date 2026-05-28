"""Centralized application settings loaded from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_HOURS: int = 168
    AES_KEY: str = ""
    BRIDGE_SECRET: str = "change-me"

    LLM_PROVIDER: Literal["anthropic", "openai", "groq"] = "groq"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-large"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    DATABASE_URL: str = "postgresql+asyncpg://gaia:gaia_dev_password@postgres:5432/gaia"
    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB: str = "gaia"
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: str = ""
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    WHATSAPP_BRIDGE_URL: str = "http://whatsapp-bridge:4000"
    BACKEND_INTERNAL_URL: str = "http://backend:8000"

    CORS_ORIGINS: str = "http://localhost:3000"

    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DIM: int = 1024

    HISTORY_TOP_K: int = 12
    RECENT_TURNS: int = 8
    HISTORY_MAX_PER_CONTACT: int = 1000

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
