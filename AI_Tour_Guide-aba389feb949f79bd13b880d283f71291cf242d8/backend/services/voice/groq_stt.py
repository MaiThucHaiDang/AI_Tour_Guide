"""Groq Speech-to-Text provider using the official Groq SDK.

Moved from: part4/backend/services/voice/groq_stt.py
Logic preserved exactly — only import paths updated.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

from groq import Groq

from services.ai.interfaces import BaseSTT
from core.config import settings


class GroqSTTProvider(BaseSTT):
    """Speech-to-Text implementation powered by Groq's Whisper models."""

    _CONTENT_TYPE_MAP = {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/mp4": ".mp4",
        "audio/m4a": ".m4a",
        "audio/x-m4a": ".m4a",
    }

    def __init__(self) -> None:
        api_key = settings.GROQ_API_KEY.strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        self._client = Groq(api_key=api_key)

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str | None = None,
        content_type: str | None = None,
        language_hint: str | None = None,
    ) -> tuple[str, str]:
        temp_path = None
        try:
            suffix = self._resolve_suffix(filename, content_type)
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            def _do_transcribe() -> Any:
                with open(temp_path, "rb") as audio_file:
                    request = {
                        "model": "whisper-large-v3",
                        "file": audio_file,
                        "temperature": 0.0,
                        "response_format": "verbose_json",
                    }
                    if language_hint:
                        request["language"] = language_hint
                    prompt = self._build_prompt(language_hint)
                    if prompt:
                        request["prompt"] = prompt
                    return self._client.audio.transcriptions.create(**request)

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

    @classmethod
    def _resolve_suffix(cls, filename: str | None, content_type: str | None) -> str:
        if filename:
            ext = Path(filename).suffix.lower()
            if ext:
                return ext
        if content_type:
            normalized = content_type.split(";")[0].strip().lower()
            return cls._CONTENT_TYPE_MAP.get(normalized, ".wav")
        return ".wav"

    @staticmethod
    def _build_prompt(language_hint: str | None) -> str | None:
        hints = settings.STT_DOMAIN_HINTS.strip()
        if not hints:
            return None
        language_note = "" if not language_hint else f" Language hint: {language_hint}."
        return f"Tourism and heritage terms: {hints}.{language_note}".strip()
