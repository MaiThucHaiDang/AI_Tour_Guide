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
from core.config import get_settings, settings

MAX_NO_SPEECH_PROB = 0.6
MIN_AVG_LOGPROB = -1.0
MAX_COMPRESSION_RATIO = 2.8


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
        current_settings = get_settings()
        api_key = current_settings.GROQ_API_KEY.strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        self._client = Groq(api_key=api_key)
        self._model = current_settings.GROQ_STT_MODEL.strip()

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
                        "model": self._model,
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
            if self._is_low_confidence_transcription(response, text):
                return "", detected_lang
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
    def _is_low_confidence_transcription(cls, response: Any, text: str) -> bool:
        """Reject likely silence/noise hallucinations using Whisper segment metadata."""
        if not (text or "").strip():
            return True

        segments = cls._extract_segments(response)
        if not segments:
            return False

        no_speech_probs = cls._segment_values(segments, "no_speech_prob")
        avg_logprobs = cls._segment_values(segments, "avg_logprob")
        compression_ratios = cls._segment_values(segments, "compression_ratio")

        if no_speech_probs and min(no_speech_probs) >= MAX_NO_SPEECH_PROB:
            return True
        if avg_logprobs and max(avg_logprobs) <= MIN_AVG_LOGPROB:
            return True
        if compression_ratios and min(compression_ratios) >= MAX_COMPRESSION_RATIO:
            return True
        return False

    @staticmethod
    def _extract_segments(response: Any) -> list[Any]:
        if isinstance(response, dict):
            segments = response.get("segments", [])
        else:
            segments = getattr(response, "segments", [])
        return list(segments or [])

    @staticmethod
    def _segment_values(segments: list[Any], key: str) -> list[float]:
        values: list[float] = []
        for segment in segments:
            raw_value = segment.get(key) if isinstance(segment, dict) else getattr(segment, key, None)
            if raw_value is None:
                continue
            try:
                values.append(float(raw_value))
            except (TypeError, ValueError):
                continue
        return values

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
