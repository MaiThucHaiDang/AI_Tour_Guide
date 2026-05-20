"""Health check API router."""

from __future__ import annotations

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


@router.get("/")
async def root():
    """Root endpoint for basic connectivity check."""
    return {"status": "ok"}
