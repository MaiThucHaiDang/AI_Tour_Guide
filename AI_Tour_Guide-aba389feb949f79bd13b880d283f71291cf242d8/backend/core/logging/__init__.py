"""Re-export logging setup for backward-compatible imports.

Usage: ``from core.logging import setup_logging``
"""
from core.logging.logger import setup_logging

__all__ = ["setup_logging"]
