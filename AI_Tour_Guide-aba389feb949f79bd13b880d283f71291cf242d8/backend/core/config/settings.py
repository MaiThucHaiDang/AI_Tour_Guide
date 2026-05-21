"""Centralized configuration using Pydantic Settings."""

from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

# .parent = config/, .parent.parent = core/, .parent.parent.parent = backend/
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_ROOT.parent


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    LLM_PROVIDER_ORDER: str = "gemini,groq"

    VOICE_MAX_TURNS: int = 6
    VOICE_SESSION_TTL_SECONDS: int = 3600
    VOICE_MAX_TURN_CHARS: int = 240
    STT_DOMAIN_HINTS: str = ""

    EDGE_TTS_VOICE_VI: str = "vi-VN-HoaiMyNeural"
    EDGE_TTS_VOICE_EN: str = "en-US-AriaNeural"

    RATE_LIMIT: str = "30/minute"
    CORS_ORIGINS: list[str] = ["https://localhost:5173", "http://localhost:5173"]

    model_config = {
        "env_file": [str(_BACKEND_ROOT / ".env"), str(_PROJECT_ROOT / ".env")],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    @property
    def llm_provider_list(self) -> list[str]:
        return [p.strip().lower() for p in self.LLM_PROVIDER_ORDER.split(",") if p.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
