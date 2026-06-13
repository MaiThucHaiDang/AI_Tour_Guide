"""Edge TTS provider using the edge-tts asyncio library.

Moved from: part4/backend/services/voice/edge_tts_provider.py
Logic preserved exactly.
"""

from __future__ import annotations

import hashlib
import logging
import asyncio
import time

import edge_tts

from services.ai.interfaces import BaseTTS
from core.config import settings

_LOGGER = logging.getLogger(__name__)
_TTS_CACHE_MAX_ITEMS = 96
_TTS_CACHE: dict[str, bytes] = {}
_TTS_BREAKER_UNTIL = 0.0
_TTS_BREAKER_DURATION = 60.0  # seconds


class EdgeTTSProvider(BaseTTS):
    """Text-to-Speech implementation backed by Microsoft Edge TTS."""

    async def synthesize(self, text: str, lang: str) -> bytes:
        global _TTS_BREAKER_UNTIL

        voice_map = {
            "vi": settings.EDGE_TTS_VOICE_VI,
            "en": settings.EDGE_TTS_VOICE_EN,
        }
        voice = voice_map.get(lang, settings.EDGE_TTS_VOICE_EN)
        cache_key = self._cache_key(text, lang, voice)
        cached = _TTS_CACHE.get(cache_key)
        if cached is not None:
            return cached

        # Check circuit breaker
        now = time.time()
        if now < _TTS_BREAKER_UNTIL:
            _LOGGER.warning(
                "Edge TTS circuit breaker is active (remains %.1fs). Skipping TTS synthesis.",
                _TTS_BREAKER_UNTIL - now
            )
            return b""

        try:
            communicator = edge_tts.Communicate(
                text=text,
                voice=voice,
                connect_timeout=3,
                receive_timeout=10
            )
            audio_chunks = bytearray()
            async for chunk in communicator.stream():
                if chunk.get("type") == "audio" and "data" in chunk:
                    audio_chunks.extend(chunk["data"])

            audio_bytes = bytes(audio_chunks)
        except asyncio.CancelledError:
            # Orchestrator timeout cancelled us — NOT a network issue.
            # Do NOT trip breaker; just return empty so frontend uses Web Speech.
            _LOGGER.info("Edge TTS synthesis cancelled by orchestrator timeout.")
            return b""
        except Exception as e:
            _LOGGER.error(
                "Edge TTS synthesis failed: %s. Tripping circuit breaker for %ds.",
                e, int(_TTS_BREAKER_DURATION),
            )
            _TTS_BREAKER_UNTIL = time.time() + _TTS_BREAKER_DURATION
            return b""

        if audio_bytes:
            if len(_TTS_CACHE) >= _TTS_CACHE_MAX_ITEMS:
                oldest_key = next(iter(_TTS_CACHE))
                _TTS_CACHE.pop(oldest_key, None)
            _TTS_CACHE[cache_key] = audio_bytes
        return audio_bytes

    @staticmethod
    def _cache_key(text: str, lang: str, voice: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{lang}:{voice}:{digest}"
