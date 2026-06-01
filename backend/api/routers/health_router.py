"""Health check API router."""

from __future__ import annotations

import asyncio
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from core.config import settings
from core.database import engine

router = APIRouter(tags=["Health"])
_LOGGER = logging.getLogger(__name__)


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

    checks["gemini_api_key"] = "configured" if settings.GEMINI_API_KEY.strip() else "missing"
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
    checks: dict[str, dict] = {}

    # 1. Gemini API — try to list models
    try:
        from google import genai
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            checks["gemini"] = {"status": "not_configured"}
        else:
            client = genai.Client(api_key=api_key)
            models = await asyncio.to_thread(lambda: list(client.models.list()))
            model_names = [m.name for m in models[:5]] if models else []
            checks["gemini"] = {
                "status": "ok",
                "models_found": len(models) if models else 0,
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
        from core.dependencies import get_tts_provider
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

