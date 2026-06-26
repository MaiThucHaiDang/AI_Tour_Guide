"""Health check API router."""

from __future__ import annotations

import asyncio
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from core.config import settings
from core.database import engine
from core.dependencies import get_tts_provider

router = APIRouter(tags=["Health"])
_LOGGER = logging.getLogger(__name__)


def _configured_gemini_keys() -> list[str]:
    configured = getattr(settings, "gemini_api_key_list", None)
    if isinstance(configured, list):
        return configured

    keys: list[str] = []
    for attr in ("GEMINI_API_KEY", "GEMINI_API_KEY_2"):
        value = getattr(settings, attr, "")
        if isinstance(value, str):
            normalized = value.strip()
            if normalized and normalized not in keys:
                keys.append(normalized)

    extra = getattr(settings, "GEMINI_API_KEYS", "")
    if isinstance(extra, str):
        for value in extra.split(","):
            normalized = value.strip()
            if normalized and normalized not in keys:
                keys.append(normalized)
    return keys


@router.get("/api/v1/health")
async def health_check():
    """Backward-compatible health check endpoint."""
    return {
        "status": "ok",
        "service": "AI Tour Guide Backend v2",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/api/v1/health/live")
async def liveness_check():
    """Liveness check: process is up."""
    return {
        "status": "ok",
        "service": "AI Tour Guide Backend v2",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/api/v1/health/ready")
async def readiness_check():
    """Readiness check: dependencies needed for the web demo are reachable/configured."""
    checks: dict[str, str] = {}
    status_code = 200

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        _LOGGER.warning("Readiness database check failed: %s", exc)
        checks["database"] = "unavailable"
        status_code = 503

    gemini_api_keys = _configured_gemini_keys()
    checks["gemini_api_key"] = "configured" if gemini_api_keys else "missing"
    checks["gemini_api_key_count"] = str(len(gemini_api_keys))
    checks["groq_api_key"] = "configured" if settings.GROQ_API_KEY.strip() else "missing"

    if checks["gemini_api_key"] == "missing":
        status_code = 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if status_code == 200 else "degraded",
            "service": "AI Tour Guide Backend v2",
            "environment": settings.ENVIRONMENT,
            "checks": checks,
        },
    )


@router.get("/api/v1/health/ai")
async def ai_connectivity_check():
    """Deep health check: actually ping each AI service to verify connectivity."""
    if settings.ENVIRONMENT == "production":
        return JSONResponse(status_code=403, content={"status": "disabled_in_production"})
        
    checks: dict[str, dict] = {}

    # 1. Gemini API — try to list models for each configured key
    try:
        from google import genai
        api_keys = _configured_gemini_keys()
        if not api_keys:
            checks["gemini"] = {"status": "not_configured"}
        else:
            key_checks = []
            for index, api_key in enumerate(api_keys, start=1):
                client = genai.Client(api_key=api_key)
                models = await asyncio.to_thread(lambda: list(client.models.list()))
                key_checks.append({
                    "key": f"gemini_key_{index}",
                    "status": "ok",
                    "models_found": len(models) if models else 0,
                })
            first_models = await asyncio.to_thread(lambda: list(genai.Client(api_key=api_keys[0]).models.list()))
            model_names = [m.name for m in first_models[:5]] if first_models else []
            checks["gemini"] = {
                "status": "ok",
                "configured_keys": len(api_keys),
                "keys": key_checks,
                "sample_models": model_names,
            }
    except Exception as exc:
        _LOGGER.warning("Gemini health check failed: %s", exc)
        checks["gemini"] = {"status": "error", "detail": str(exc)}

    # 2. Groq API — try to list models
    try:
        api_key = settings.GROQ_API_KEY.strip()
        if not api_key:
            checks["groq"] = {"status": "not_configured"}
        else:
            from groq import AsyncGroq
            groq_client = AsyncGroq(api_key=api_key)
            models_response = await groq_client.models.list()
            model_ids = [m.id for m in models_response.data[:5]] if models_response.data else []
            checks["groq"] = {
                "status": "ok",
                "models_found": len(models_response.data) if models_response.data else 0,
                "sample_models": model_ids,
            }
    except Exception as exc:
        _LOGGER.warning("Groq health check failed: %s", exc)
        checks["groq"] = {"status": "error", "detail": str(exc)}

    # 3. HuggingFace Embedding API — test embedding
    try:
        api_key = settings.HUGGINGFACE_API_KEY.strip() if hasattr(settings, 'HUGGINGFACE_API_KEY') else ""
        if not api_key:
            checks["huggingface_embedding"] = {"status": "not_configured"}
        else:
            from services.ai.embedding_service import EmbeddingService
            test_vector = await EmbeddingService.get_embedding("test connection")
            checks["huggingface_embedding"] = {
                "status": "ok",
                "vector_dimensions": len(test_vector) if test_vector else 0,
            }
    except Exception as exc:
        _LOGGER.warning("HuggingFace embedding health check failed: %s", exc)
        checks["huggingface_embedding"] = {"status": "error", "detail": str(exc)}

    # 4. Database + pgvector
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
        checks["database"] = {"status": "ok", "ping": row == 1}
    except Exception as exc:
        _LOGGER.warning("Database health check failed: %s", exc)
        checks["database"] = {"status": "error", "detail": str(exc)}

    # 5. Edge TTS (local, no API key needed)
    try:
        tts = get_tts_provider()
        if tts is None:
            checks["edge_tts"] = {"status": "not_configured"}
        else:
            test_audio = await tts.synthesize("test", "en")
            checks["edge_tts"] = {
                "status": "ok",
                "test_audio_bytes": len(test_audio) if test_audio else 0,
            }
    except Exception as exc:
        _LOGGER.warning("Edge TTS health check failed: %s", exc)
        checks["edge_tts"] = {"status": "error", "detail": str(exc)}

    all_ok = all(c.get("status") == "ok" for c in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "status": "healthy" if all_ok else "degraded",
            "service": "AI Tour Guide Backend v2",
            "environment": settings.ENVIRONMENT,
            "checks": checks,
        },
    )


@router.get("/")
async def root():
    """Root endpoint for basic connectivity check."""
    return {"status": "ok"}

