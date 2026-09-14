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
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""
    GEMINI_API_KEY_4: str = ""
    GEMINI_API_KEYS: str = ""
    GROQ_API_KEY: str = ""
    GROQ_API_KEYS: str = ""
    HUGGINGFACE_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    LLM_PROVIDER_ORDER: str = "gemini, groq"
    GEMINI_TEXT_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_TEXT_MODEL_2: str = "gemini-3.1-flash-lite"
    GEMINI_TEXT_MODELS: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"
    GEMINI_VISION_MODEL: str = "gemini-3.5-flash-lite"
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_STT_MODEL: str = "whisper-large-v3"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    LLM_MAX_TOKENS_FOLLOWUP: int = 800
    LLM_MAX_TOKENS_IMAGE: int = 650
    VISION_CONFIDENCE_THRESHOLD: float = 0.6
    VISION_TIMEOUT_SECONDS: int = 40

    TEXT_MAX_CHARS: int = 5000
    IMAGE_MAX_BYTES: int = 5_000_000
    AUDIO_MAX_BYTES: int = 8_000_000
    UPLOADS_DIR: str = str(_BACKEND_ROOT / "uploads")
    BLOG_COVER_MAX_BYTES: int = 5_000_000

    VOICE_MAX_TURNS: int = 6
    VOICE_SESSION_TTL_SECONDS: int = 3600
    VOICE_MAX_TURN_CHARS: int = 2000
    STT_DOMAIN_HINTS: str = ""

    EDGE_TTS_VOICE_VI: str = "vi-VN-HoaiMyNeural"
    EDGE_TTS_VOICE_EN: str = "en-US-AriaNeural"

    RATE_LIMIT: str = "30/minute"
    CORS_ORIGINS: list[str] = ["https://localhost:5173", "http://localhost:5173"]

    VNPAY_TMN_CODE: str = ""
    VNPAY_HASH_SECRET: str = ""
    VNPAY_RETURN_URL: str = "http://localhost:5173/?view=paymentResult"
    VNPAY_PAYMENT_URL: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"

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
    def gemini_api_key_list(self) -> list[str]:
        keys: list[str] = []
        for key in (
            self.GEMINI_API_KEY,
            self.GEMINI_API_KEY_2,
            self.GEMINI_API_KEY_3,
            self.GEMINI_API_KEY_4,
        ):
            normalized = key.strip()
            if normalized and normalized not in keys:
                keys.append(normalized)
        for key in self.GEMINI_API_KEYS.split(","):
            normalized = key.strip()
            if normalized and normalized not in keys:
                keys.append(normalized)
        return keys

    @property
    def groq_api_key_list(self) -> list[str]:
        keys: list[str] = []
        for key in (self.GROQ_API_KEY, *self.GROQ_API_KEYS.split(",")):
            normalized = key.strip()
            if normalized and normalized not in keys:
                keys.append(normalized)
        return keys

    @property
    def gemini_text_model_list(self) -> list[str]:
        primary = self.GEMINI_TEXT_MODEL.strip() or "gemini-2.5-flash-lite"
        models: list[str] = [primary]

        backup = self.GEMINI_TEXT_MODEL_2.strip()
        if backup:
            models.append(backup)

        for model in self.GEMINI_TEXT_MODELS.split(","):
            normalized = model.strip()
            if normalized:
                models.append(normalized)
        return models

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in {"production", "prod"}

    def validate_runtime(self) -> None:
        """Fail fast for configuration that should never be missing in production."""
        if not self.is_production:
            return

        missing = []
        if not self.gemini_api_key_list:
            missing.append("GEMINI_API_KEY")
        if not self.groq_api_key_list:
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
