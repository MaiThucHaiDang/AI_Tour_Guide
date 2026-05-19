"""Unified FastAPI application entrypoint.

Merges both Backend 1 (port 8000, vision) and Backend 2 (port 8001, voice)
into a single application running on port 8000.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.logging import setup_logging
from middleware.error_handler import global_exception_handler

# Setup logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


# ─── Rate Limiter ────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Tour Guide Backend starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("Routers: vision (/api/v1/recognize), voice (/api/v1/voice/chat)")
    yield
    logger.info("Backend shutting down.")


# ─── Application ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Tour Guid + Voice AIe - Unified Backend API",
    description="Vision Tour Guide backend",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Register Routers ────────────────────────────────────────────────────────
from api.routers.health_router import router as health_router
from api.routers.vision_router import router as vision_router
from api.routers.voice_router import router as voice_router
from api.routers.chat_router import router as chat_router

app.include_router(health_router)
app.include_router(vision_router)
app.include_router(voice_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
