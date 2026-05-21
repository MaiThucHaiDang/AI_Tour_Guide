"""Voice orchestration pipeline for STT, LLM, and TTS services.

Moved from: part4/backend/services/voice/voice_pipeline.py
Logic preserved exactly — only import paths updated.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
import logging
import unicodedata
from typing import Any

from services.ai.interfaces import BaseLLM, BaseSTT, BaseTTS
from utils.language_manager import LanguageManager
from services.memory.conversation_memory import ConversationMemory
from repositories.artifact_repository import canonicalize_transcript_entities


_LOGGER = logging.getLogger(__name__)

STT_TIMEOUT_SECONDS = 20
LLM_TIMEOUT_SECONDS = 20
TTS_TIMEOUT_SECONDS = 20
MIN_AUDIO_BYTES = 800
MIN_TRANSCRIPT_CHARS = 2
_NO_CONTEXT_MARKERS = {
    "No matching artifact found in database.",
    "Database is temporarily unavailable.",
}
_SMALL_TALK_KEYWORDS = {
    "hello", "hi", "hey", "xin chao", "chao", "cam on",
    "thanks", "thank you", "ban khoe khong", "how are you",
    "ban la ai", "ban ten gi", "goodbye", "bye",
}
_ARTIFACT_KEYWORDS = {
    "di tich", "hien vat", "di danh", "lang", "cung", "bao tang",
    "monument", "artifact", "museum", "temple", "palace", "gate", "citadel",
}


@dataclass
class VoicePipelineResult:
    audio_bytes: bytes
    transcript: str
    response_text: str
    lang: str
    detected_lang: str


class VoiceOrchestrator:
    """Coordinate voice request processing through injected services."""

    def __init__(
        self,
        stt: BaseSTT | None,
        llm: BaseLLM | None,
        tts: BaseTTS | None,
        db_lookup: Callable[[str, str], Coroutine[Any, Any, str] | str] | None = None,
        memory: ConversationMemory | None = None,
    ) -> None:
        self._stt = stt
        self._llm = llm
        self._tts = tts
        self._language_manager = LanguageManager()
        self._db_lookup = db_lookup
        self._memory = memory or ConversationMemory()

    async def process_voice_request(
        self,
        audio_bytes: bytes,
        lang_param: str,
        audio_filename: str | None = None,
        audio_content_type: str | None = None,
        session_id: str | None = None,
        artifact_hint: str | None = None,
        prefetched_context: str | None = None,
    ) -> VoicePipelineResult:
        """Process an audio request and return synthesized audio and text."""
        requested_lang = lang_param.strip().lower()
        context = self._language_manager.setup_context(requested_lang)
        lang_code = context["lang_code"]

        if not audio_bytes or len(audio_bytes) < MIN_AUDIO_BYTES:
            return await self._respond_not_heard(lang_code, "")

        try:
            if self._stt is None:
                raise RuntimeError("STT provider is not configured.")
            text_query, detected_lang = await asyncio.wait_for(
                self._stt.transcribe(
                    audio_bytes, audio_filename, audio_content_type, lang_code,
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
            return await self._respond_not_heard(lang_code, detected_lang or "")

        text_query = await canonicalize_transcript_entities(text_query, lang_code)

        detected = (detected_lang or "").strip().lower()
        if detected and detected != lang_code:
            _LOGGER.info(
                "Detected language '%s' differs from requested '%s'",
                detected, lang_code,
            )

        intent = self._classify_intent(text_query)
        cleaned_hint = (artifact_hint or "").strip()

        db_data: str | None = None
        try:
            if prefetched_context is not None:
                db_data = prefetched_context
            elif self._db_lookup:
                db_data = await self._call_db_lookup(text_query, context["db_field"])
        except Exception as exc:
            _LOGGER.exception("Voice database lookup failed")
            raise RuntimeError(f"Database lookup failed: {exc}") from exc

        if self._is_unhelpful_context(db_data) and cleaned_hint and self._db_lookup:
            try:
                db_data = await self._call_db_lookup(cleaned_hint, context["db_field"])
            except Exception as exc:
                _LOGGER.warning("Voice database lookup with hint failed: %s", exc)

        response_text: str | None = None
        context_data: str | None = None
        history_context = self._memory.format_history(session_id or "")

        if self._is_unhelpful_context(db_data):
            # Cải tiến 3: Fallback to GENERAL_CHAT if it's small talk or no specific artifact found
            if intent == "small_talk" or intent == "unknown":
                context_data = self._build_general_chat_context(history_context)
            else:
                context_data = self._build_missing_context(cleaned_hint, history_context)
        else:
            context_data = self._build_db_context(db_data, history_context, cleaned_hint)

        if context_data is not None:
            try:
                if self._llm is None:
                    raise RuntimeError("LLM provider is not configured.")
                response_text = await asyncio.wait_for(
                    self._llm.generate_response(text_query, context_data, lang_code),
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            except TimeoutError as exc:
                _LOGGER.exception("Voice LLM step timed out")
                response_text = self._llm_fallback_message(lang_code, not self._is_unhelpful_context(db_data))
            except Exception as exc:
                _LOGGER.exception("Voice LLM step failed")
                response_text = self._llm_fallback_message(lang_code, not self._is_unhelpful_context(db_data))

        if response_text is None or not response_text.strip():
            response_text = self._no_context_message(lang_code)

        if session_id:
            self._memory.add_turn(session_id, "user", text_query)
            self._memory.add_turn(session_id, "assistant", response_text)

        synthesized_audio = await self._synthesize_response(response_text, lang_code)

        return VoicePipelineResult(
            audio_bytes=synthesized_audio,
            transcript=text_query,
            response_text=response_text,
            lang=lang_code,
            detected_lang=detected,
        )

    def _mock_get_db_data(self, text: str, db_field: str) -> str:
        return f"Mock data for '{text}' from {db_field}."

    async def _call_db_lookup(self, text: str, db_field: str) -> str:
        if self._db_lookup is None:
            return ""
        result = self._db_lookup(text, db_field)
        if inspect.isawaitable(result):
            return await result
        return result

    @staticmethod
    def _is_unhelpful_context(context_data: str) -> bool:
        if not context_data:
            return True
        trimmed = context_data.strip()
        if not trimmed:
            return True
        return trimmed in _NO_CONTEXT_MARKERS

    @staticmethod
    def _no_context_message(lang_code: str) -> str:
        if lang_code == "vi":
            return (
                "Xin loi, toi chua tim thay thong tin phu hop. "
                "Ban co the noi ro ten di tich hoac hien vat khong?"
            )
        return (
            "Sorry, I could not find relevant information. "
            "Please say the monument or artifact name more clearly."
        )

    @staticmethod
    def _not_heard_message(lang_code: str) -> str:
        if lang_code == "vi":
            return "Toi chua nghe ro, hay noi lai nhe."
        return "I did not catch that. Please say it again."

    async def _respond_not_heard(
        self, lang_code: str, detected_lang: str
    ) -> VoicePipelineResult:
        response_text = self._not_heard_message(lang_code)
        synthesized_audio = await self._synthesize_response(response_text, lang_code)
        return VoicePipelineResult(
            audio_bytes=synthesized_audio, transcript="",
            response_text=response_text, lang=lang_code,
            detected_lang=detected_lang,
        )

    async def _synthesize_response(self, text: str, lang_code: str) -> bytes:
        try:
            if self._tts is None:
                return b""
            return await asyncio.wait_for(
                self._tts.synthesize(text, lang_code), timeout=TTS_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            _LOGGER.exception("Voice TTS step timed out")
            return b""
        except Exception as exc:
            _LOGGER.exception("Voice TTS step failed")
            return b""

    @staticmethod
    def _build_db_context(
        db_data: str, history_context: str, artifact_hint: str | None
    ) -> str:
        parts = []
        if history_context:
            parts.append("CONVERSATION_HISTORY:\n" + history_context)
        if artifact_hint:
            parts.append("ARTIFACT_HINT:\n" + artifact_hint)
        parts.append("DB_CONTEXT:\n" + db_data)
        return "\n\n".join(parts)

    @staticmethod
    def _build_general_chat_context(history_context: str) -> str:
        parts = [
            "GENERAL_CHAT: You are a friendly tour guide. Keep it short. "
            "Avoid making up historical facts. If asked about an artifact, "
            "ask for the exact name.",
        ]
        if history_context:
            parts.append("CONVERSATION_HISTORY:\n" + history_context)
        return "\n\n".join(parts)

    @staticmethod
    def _build_missing_context(artifact_hint: str, history_context: str) -> str:
        parts = [
            "DB_CONTEXT:\n<NO_CONTEXT>",
            "CONTEXT_NOTE: Database has no matching artifact for the query.",
        ]
        if artifact_hint:
            parts.append("ARTIFACT_HINT:\n" + artifact_hint)
        if history_context:
            parts.append("CONVERSATION_HISTORY:\n" + history_context)
        return "\n\n".join(parts)

    @staticmethod
    def _llm_fallback_message(lang_code: str, has_database_context: bool) -> str:
        if lang_code == "en":
            if has_database_context:
                return (
                    "I heard your question and found related artifact data, but the AI answer service "
                    "is temporarily unavailable. Please try a shorter question about year, author, "
                    "location, or meaning."
                )
            return (
                "I heard your question, but the AI answer service is temporarily unavailable and "
                "I do not have a matching artifact in the current collection."
            )
        if has_database_context:
            return (
                "Mình đã nghe được câu hỏi và tìm thấy dữ liệu liên quan, nhưng dịch vụ tạo câu trả lời "
                "đang tạm thời không sẵn sàng. Bạn có thể hỏi ngắn hơn về năm xây dựng, tác giả, vị trí "
                "hoặc ý nghĩa."
            )
        return (
            "Mình đã nghe được câu hỏi, nhưng dịch vụ tạo câu trả lời đang tạm thời không sẵn sàng "
            "và chưa tìm thấy hiện vật khớp trong dữ liệu hiện tại."
        )

    @classmethod
    def _classify_intent(cls, text: str) -> str:
        normalized = cls._normalize_text(text)
        if any(keyword in normalized for keyword in _ARTIFACT_KEYWORDS):
            return "artifact"
        if any(keyword in normalized for keyword in _SMALL_TALK_KEYWORDS):
            return "small_talk"
        return "unknown"

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = unicodedata.normalize("NFD", text or "")
        stripped = "".join(
            char for char in normalized if unicodedata.category(char) != "Mn"
        )
        return " ".join(stripped.lower().split())
