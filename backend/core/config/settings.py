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
    HUGGINGFACE_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    LLM_PROVIDER_ORDER: str = "gemini, groq"
    GEMINI_TEXT_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"
    GEMINI_VISION_MODEL: str = "gemini-2.5-flash"
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_STT_MODEL: str = "whisper-large-v3"
    LLM_TEMPERATURE: float = 0.6
    LLM_MAX_TOKENS: int = 400
    VISION_CONFIDENCE_THRESHOLD: float = 0.6

    TEXT_MAX_CHARS: int = 1200
    IMAGE_MAX_BYTES: int = 5_000_000
    AUDIO_MAX_BYTES: int = 8_000_000

    VOICE_MAX_TURNS: int = 6
    VOICE_SESSION_TTL_SECONDS: int = 3600
    VOICE_MAX_TURN_CHARS: int = 1000
    STT_DOMAIN_HINTS: str = ""

    EDGE_TTS_VOICE_VI: str = "vi-VN-HoaiMyNeural"
    EDGE_TTS_VOICE_EN: str = "en-US-AriaNeural"
    EDGE_TTS_RATE: str = "+0%"

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

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in {"production", "prod"}

    def validate_runtime(self) -> None:
        """Fail fast for configuration that should never be missing in production."""
        if not self.is_production:
            return

        missing = []
        if not self.GEMINI_API_KEY.strip():
            missing.append("GEMINI_API_KEY")
        if not self.GROQ_API_KEY.strip():
            missing.append("GROQ_API_KEY")
        if not self.DATABASE_URL.strip():
            missing.append("DATABASE_URL")
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required production settings: {joined}")


@lru_cache()
def get_settings() -> Settings:
    current_settings = Settings()
    current_settings.validate_runtime()
    return current_settings


settings: Settings = get_settings()
