"""Unified FastAPI application entrypoint.

Merges both Backend 1 (port 8000, vision) and Backend 2 (port 8001, voice)
into a single application running on port 8000.
"""

from __future__ import annotations

import logging
from time import perf_counter
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from core.config import settings
from core.cache import setup_cache
from core.logging import setup_logging
from core.observability import increment, observe_duration, snapshot
from core.security import limiter, rate_limit_exceeded_handler
from middleware.error_handler import global_exception_handler
from services.ai.embedding_service import EmbeddingService

# Setup logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Tour Guide Backend starting...")
    try:
        setup_cache()
        logger.info("Cache initialized successfully")
    except Exception as e:
        logger.error("Cache initialization failed: %s", e, exc_info=True)
        # Continue startup even if cache fails

    try:
        from services.voice.intro_service import intro_service
        await intro_service.initialize()
        logger.info("Pre-generated intro cache initialized successfully")
    except Exception as e:
        logger.error("Pre-generated intro cache initialization failed: %s", e, exc_info=True)

    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Routers: vision (/api/v1/recognize), voice (/api/v1/voice/chat)")
    yield
    logger.info("Backend shutting down.")


# ─── Application ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Tour Guide - Unified Backend API",
    description="Smart tourism backend for vision, voice, chat, and artifact context",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    detail = exc.detail if isinstance(exc.detail, str) else "Yêu cầu không hợp lệ."
    error_code = "HTTP_ERROR"
    if exc.status_code == 413:
        error_code = "PAYLOAD_TOO_LARGE"
    elif exc.status_code == 429:
        error_code = "RATE_LIMIT_EXCEEDED"
    elif exc.status_code >= 500:
        error_code = "SERVER_ERROR"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": error_code,
            "message": detail,
            "detail": detail,
            "request_id": request_id,
        },
        headers=getattr(exc, "headers", None),
    )


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    started_at = perf_counter()
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    route_key = f"{request.method} {request.url.path}"
    increment(f"http.{response.status_code}")
    observe_duration(route_key, started_at)
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (perf_counter() - started_at) * 1000,
    )
    return response

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
from api.routers.feedback_router import router as feedback_router
from api.routers.map_router import router as map_router
from api.routers.game_router import router as game_router

app.include_router(health_router)
app.include_router(vision_router)
app.include_router(voice_router)
app.include_router(chat_router)
app.include_router(feedback_router)
app.include_router(map_router)
app.include_router(game_router)


@app.get("/api/v1/metrics")
async def metrics_snapshot():
    return snapshot()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
