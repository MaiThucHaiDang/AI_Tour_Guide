"""Request validation helpers for costly AI endpoints."""

from __future__ import annotations

import base64
import binascii

from fastapi import HTTPException

import logging
from core.config import settings

logger = logging.getLogger(__name__)


def normalize_lang(lang: str | None) -> str:
    """Validate and normalize language parameter."""
    if lang:
        lang = lang.strip().lower()
    if lang not in ("vi", "en"):
        logger.warning("Invalid language code: %s, defaulting to 'vi'", lang)
        return "vi"
    return lang


def validate_text_size(text: str | None) -> None:
    if text and len(text) > settings.TEXT_MAX_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Nội dung quá dài. Giới hạn hiện tại là {settings.TEXT_MAX_CHARS} ký tự.",
        )


def validate_image_base64_size(image_base64: str | None) -> None:
    if not image_base64:
        return
    encoded = _strip_data_url(image_base64)
    estimated_bytes = _estimate_base64_bytes(encoded)
    if estimated_bytes > settings.IMAGE_MAX_BYTES:
        max_mb = settings.IMAGE_MAX_BYTES / 1_000_000
        raise HTTPException(
            status_code=413,
            detail=f"Ảnh quá lớn. Vui lòng dùng ảnh dưới {max_mb:.1f} MB.",
        )


def validate_audio_size(audio_bytes: bytes | None) -> None:
    if audio_bytes is None:
        return
    if len(audio_bytes) > settings.AUDIO_MAX_BYTES:
        max_mb = settings.AUDIO_MAX_BYTES / 1_000_000
        raise HTTPException(
            status_code=413,
            detail=f"Audio quá lớn. Vui lòng ghi âm ngắn hơn hoặc dưới {max_mb:.1f} MB.",
        )


def decode_image_base64(image_base64: str) -> bytes:
    """Decode base64 image after stripping optional data URL prefix."""
    try:
        return base64.b64decode(_strip_data_url(image_base64), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 image payload.") from exc


def _strip_data_url(image_base64: str) -> str:
    if "," in image_base64:
        return image_base64.split(",", 1)[1]
    return image_base64


def _estimate_base64_bytes(encoded: str) -> int:
    compact = "".join(encoded.split())
    if not compact:
        return 0
    padding = 2 if compact.endswith("==") else 1 if compact.endswith("=") else 0
    return max(0, (len(compact) * 3 // 4) - padding)
