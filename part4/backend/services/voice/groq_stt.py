"""Groq Speech-to-Text provider using the official Groq SDK."""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import Any

from groq import Groq

from services.voice.interfaces import BaseSTT


class GroqSTTProvider(BaseSTT):
    """Speech-to-Text implementation powered by Groq's Whisper models."""

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        self._client = Groq(api_key=api_key)

    async def transcribe(self, audio_bytes: bytes) -> tuple[str, str]:
        """Transcribe audio bytes using Groq's Whisper model.

        Args:
            audio_bytes: The audio data in bytes format.

        Returns:
            A tuple containing the transcribed text and detected language code.
        """
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            def _do_transcribe() -> Any:
                with open(temp_path, "rb") as audio_file:
                    return self._client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=audio_file,
                    )

            response = await asyncio.to_thread(_do_transcribe)
            text = self._extract_text(response)
            detected_lang = self._extract_language(response)
            return text, detected_lang
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    @staticmethod
    def _extract_text(response: Any) -> str:
        if isinstance(response, dict):
            return response.get("text", "")
        return getattr(response, "text", "") or ""

    @staticmethod
    def _extract_language(response: Any) -> str:
        if isinstance(response, dict):
            return response.get("language", "")
        return getattr(response, "language", "") or ""
