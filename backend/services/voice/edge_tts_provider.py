"""Edge TTS provider using the edge-tts asyncio library.

Moved from: part4/backend/services/voice/edge_tts_provider.py
Logic preserved exactly.
"""

from __future__ import annotations

import hashlib

import edge_tts

from services.ai.interfaces import BaseTTS
from core.config import settings

_TTS_CACHE_MAX_ITEMS = 96
_TTS_CACHE: dict[str, bytes] = {}


class EdgeTTSProvider(BaseTTS):
    """Text-to-Speech implementation backed by Microsoft Edge TTS."""

    async def synthesize(self, text: str, lang: str) -> bytes:
        voice_map = {
            "vi": settings.EDGE_TTS_VOICE_VI,
            "en": settings.EDGE_TTS_VOICE_EN,
        }
        voice = voice_map.get(lang, settings.EDGE_TTS_VOICE_EN)
        rate = settings.EDGE_TTS_RATE
        cache_key = self._cache_key(text, lang, voice, rate)
        cached = _TTS_CACHE.get(cache_key)
        if cached is not None:
            return cached

        communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)

        audio_chunks = bytearray()
        async for chunk in communicator.stream():
            if chunk.get("type") == "audio" and "data" in chunk:
                audio_chunks.extend(chunk["data"])

        audio_bytes = bytes(audio_chunks)
        if audio_bytes:
            if len(_TTS_CACHE) >= _TTS_CACHE_MAX_ITEMS:
                oldest_key = next(iter(_TTS_CACHE))
                _TTS_CACHE.pop(oldest_key, None)
            _TTS_CACHE[cache_key] = audio_bytes
        return audio_bytes

    @staticmethod
    def _cache_key(text: str, lang: str, voice: str, rate: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{lang}:{voice}:{rate}:{digest}"
