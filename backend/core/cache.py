"""Cache configuration and initialization using aiocache."""

from __future__ import annotations

import logging
from typing import Any

from aiocache import caches
from aiocache.serializers import JsonSerializer

from core.config import settings

_LOGGER = logging.getLogger(__name__)


def setup_cache() -> None:
    """Initialize the cache configuration."""
    cache_config = {
        "default": {
            "cache": "aiocache.SimpleMemoryCache",
            "serializer": {"class": JsonSerializer},
        }
    }

    # Use Redis if REDIS_URL is configured
    if settings.REDIS_URL.startswith("redis://"):
        _LOGGER.info("Using Redis cache at %s", settings.REDIS_URL)
        cache_config["default"] = {
            "cache": "aiocache.RedisCache",
            "endpoint": settings.REDIS_URL.split("//")[1].split(":")[0],
            "port": int(settings.REDIS_URL.split(":")[-1].split("/")[0]),
            "db": int(settings.REDIS_URL.split("/")[-1]) if "/" in settings.REDIS_URL.split("//")[1] else 0,
            "serializer": {"class": JsonSerializer},
            "timeout": 5, # Connection timeout
        }
    else:
        _LOGGER.warning("REDIS_URL not configured. Falling back to SimpleMemoryCache.")

    caches.set_config(cache_config)


async def get_cache(name: str = "default") -> Any:
    """Get a cache instance by name."""
    return caches.get(name)
