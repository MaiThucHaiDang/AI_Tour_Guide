"""Edge TTS provider using the edge-tts asyncio library.

Moved from: part4/backend/services/voice/edge_tts_provider.py
Logic preserved exactly.
"""

from __future__ import annotations

import edge_tts

from services.ai.interfaces import BaseTTS
from core.config import settings


class EdgeTTSProvider(BaseTTS):
    """Text-to-Speech implementation backed by Microsoft Edge TTS."""

    _VOICE_MAP = {
        "vi": settings.EDGE_TTS_VOICE_VI,
        "en": settings.EDGE_TTS_VOICE_EN,
    }

    async def synthesize(self, text: str, lang: str) -> bytes:
        voice = self._VOICE_MAP.get(lang, settings.EDGE_TTS_VOICE_EN)
        communicator = edge_tts.Communicate(text=text, voice=voice)

        audio_chunks = bytearray()
        async for chunk in communicator.stream():
            if chunk.get("type") == "audio" and "data" in chunk:
                audio_chunks.extend(chunk["data"])

        return bytes(audio_chunks)
