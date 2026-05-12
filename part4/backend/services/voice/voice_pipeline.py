"""Voice orchestration pipeline for STT, LLM, and TTS services."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging

from services.voice.interfaces import BaseLLM, BaseSTT, BaseTTS
from services.voice.language_manager import LanguageManager


_LOGGER = logging.getLogger(__name__)

STT_TIMEOUT_SECONDS = 20
LLM_TIMEOUT_SECONDS = 20
TTS_TIMEOUT_SECONDS = 20


class VoiceOrchestrator:
    """Coordinate voice request processing through injected services."""

    def __init__(
        self,
        stt: BaseSTT,
        llm: BaseLLM,
        tts: BaseTTS,
        db_lookup: Callable[[str, str], str] | None = None,
    ) -> None:
        self._stt = stt
        self._llm = llm
        self._tts = tts
        self._language_manager = LanguageManager()
        self._db_lookup = db_lookup or self._mock_get_db_data

    async def process_voice_request(
        self,
        audio_bytes: bytes,
        lang_param: str,
        audio_filename: str | None = None,
        audio_content_type: str | None = None,
    ) -> bytes:
        """Process an audio request and return synthesized response audio."""
        if not audio_bytes:
            raise ValueError("Empty audio payload.")
        # Normalize language code to short form ('vi' or 'en') for service calls
        requested_lang = lang_param.strip().lower()
        context = self._language_manager.setup_context(requested_lang)
        lang_code = context["lang_code"]

        try:
            # Transcribe audio
            text_query, detected_lang = await asyncio.wait_for(
                self._stt.transcribe(
                    audio_bytes,
                    audio_filename,
                    audio_content_type,
                ),
                timeout=STT_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            _LOGGER.exception("Voice STT step timed out")
            raise RuntimeError("STT step timed out. Please try again.") from exc
        except Exception as exc:
            _LOGGER.exception("Voice STT step failed")
            raise RuntimeError(f"STT step failed: {exc}") from exc

        if not text_query.strip():
            raise ValueError("Empty transcription. Please try again with clearer audio.")

        try:
            # Resolve DB content for the detected/selected language
            db_data = self._db_lookup(text_query, context["db_field"])
        except Exception as exc:
            _LOGGER.exception("Voice database lookup failed")
            raise RuntimeError(f"Database lookup failed: {exc}") from exc

        try:
            # LLM expects a short language code (e.g. 'en' or 'vi')
            response_text = await asyncio.wait_for(
                self._llm.generate_response(
                    text_query,
                    db_data,
                    lang_code,
                ),
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            _LOGGER.exception("Voice LLM step timed out")
            raise RuntimeError("LLM step timed out. Please try again.") from exc
        except Exception as exc:
            _LOGGER.exception("Voice LLM step failed")
            raise RuntimeError(f"LLM step failed: {exc}") from exc

        try:
            # TTS provider also expects a short language code to choose a voice
            return await asyncio.wait_for(
                self._tts.synthesize(response_text, lang_code),
                timeout=TTS_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            _LOGGER.exception("Voice TTS step timed out")
            raise RuntimeError("TTS step timed out. Please try again.") from exc
        except Exception as exc:
            _LOGGER.exception("Voice TTS step failed")
            raise RuntimeError(f"TTS step failed: {exc}") from exc

    def _mock_get_db_data(self, text: str, db_field: str) -> str:
        """Return dummy data in place of the real database lookup."""
        return f"Mock data for '{text}' from {db_field}."