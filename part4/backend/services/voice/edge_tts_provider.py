"""Edge TTS provider using the edge-tts asyncio library."""

from __future__ import annotations

import edge_tts

from services.voice.interfaces import BaseTTS


class EdgeTTSProvider(BaseTTS):
    """Text-to-Speech implementation backed by Microsoft Edge TTS."""

    _VOICE_MAP = {
        "vi": "vi-VN-HoaiMyNeural",
        "en": "en-US-AriaNeural",
    }

    async def synthesize(self, text: str, lang: str) -> bytes:
        """Synthesize text to speech using Edge TTS.

        Args:
            text: The text content to synthesize.
            lang: The language code for synthesis.

        Returns:
            The synthesized audio data in bytes.
        """
        voice = self._VOICE_MAP.get(lang, "en-US-AriaNeural")
        communicator = edge_tts.Communicate(text=text, voice=voice)

        audio_chunks = bytearray()
        async for chunk in communicator.stream():
            if chunk.get("type") == "audio" and "data" in chunk:
                audio_chunks.extend(chunk["data"])

        return bytes(audio_chunks)
