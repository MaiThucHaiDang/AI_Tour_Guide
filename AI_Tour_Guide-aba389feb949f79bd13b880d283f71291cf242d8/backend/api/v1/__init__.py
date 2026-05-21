"""API v1 — aggregates all routers under the /api/v1 prefix."""

from api.routers.health_router import router as health_router
from api.routers.vision_router import router as vision_router
from api.routers.voice_router import router as voice_router

__all__ = ["health_router", "vision_router", "voice_router"]
