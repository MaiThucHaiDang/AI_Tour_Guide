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
            # Chunking logic for long texts to avoid timeouts
            chunks = self._split_text(text, max_chars=500)
            combined_audio = bytearray()

            for chunk in chunks:
                if not chunk.strip():
                    continue
                    
                _LOGGER.info("Synthesizing chunk (%d chars): %s...", len(chunk), chunk[:30])
                communicator = edge_tts.Communicate(
                    text=chunk,
                    voice=voice,
                    connect_timeout=5,
                    receive_timeout=15
                )
                
                async for audio_chunk in communicator.stream():
                    if audio_chunk.get("type") == "audio" and "data" in audio_chunk:
                        combined_audio.extend(audio_chunk["data"])
                
                # Small pause between chunks if needed (optional)
                # await asyncio.sleep(0.1)

            audio_bytes = bytes(combined_audio)
        except asyncio.CancelledError:
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

    def _split_text(self, text: str, max_chars: int = 500) -> list[str]:
        """Split text into chunks by sentence boundaries."""
        if len(text) <= max_chars:
            return [text]

        import re
        # Split by . ! ? while keeping the delimiter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += (" " if current_chunk else "") + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    @staticmethod
    def _cache_key(text: str, lang: str, voice: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{lang}:{voice}:{digest}"
