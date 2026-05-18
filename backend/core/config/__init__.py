"""Re-export config objects for backward-compatible imports.

Usage: ``from core.config import settings``
"""
from core.config.settings import Settings, settings, get_settings

__all__ = ["Settings", "settings", "get_settings"]
