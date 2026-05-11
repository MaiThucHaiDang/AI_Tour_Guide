"""Voice orchestration pipeline for STT, LLM, and TTS services."""

from __future__ import annotations

from collections.abc import Callable

from services.voice.interfaces import BaseLLM, BaseSTT, BaseTTS
from services.voice.language_manager import LanguageManager


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

        # Transcribe audio
        text_query, detected_lang = await self._stt.transcribe(
            audio_bytes,
            audio_filename,
            audio_content_type,
        )
        if not text_query.strip():
            raise ValueError("Empty transcription. Please try again with clearer audio.")

        # Resolve DB content for the detected/selected language
        db_data = self._db_lookup(text_query, context["db_field"])

        # LLM expects a short language code (e.g. 'en' or 'vi')
        response_text = await self._llm.generate_response(
            text_query,
            db_data,
            lang_code,
        )

        # TTS provider also expects a short language code to choose a voice
        return await self._tts.synthesize(response_text, lang_code)

    def _mock_get_db_data(self, text: str, db_field: str) -> str:
        """Return dummy data in place of the real database lookup."""
        return f"Mock data for '{text}' from {db_field}."