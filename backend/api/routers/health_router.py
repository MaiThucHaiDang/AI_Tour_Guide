"""Health check API router."""

from __future__ import annotations

import logging
from fastapi import APIRouter
from core.config import settings

router = APIRouter(tags=["Health"])
_LOGGER = logging.getLogger(__name__)


@router.get("/api/v1/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "service": "AI Tour Guide Backend v2",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/")
async def root():
    """Root endpoint for basic connectivity check."""
    return {"status": "ok"}
