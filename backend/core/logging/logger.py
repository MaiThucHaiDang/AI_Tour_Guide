"""Centralized logging configuration."""

from __future__ import annotations
import logging
import sys
from core.config import settings


def setup_logging() -> None:
    """Configure application-wide logging based on settings."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Suppress noisy third-party loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )
