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
from repositories.artifact_repository import (
    canonicalize_transcript_entities,
    graph_augmented_search,
    get_artifact_context_by_id
)


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

        # Validate audio
        if not audio_bytes or len(audio_bytes) < MIN_AUDIO_BYTES:
            return await self._respond_not_heard(lang_code, "")

        # 1. STT
        if self._stt is None:
            raise RuntimeError("STT not configured")
        text_query, detected_lang = await asyncio.wait_for(
            self._stt.transcribe(
                audio_bytes, audio_filename, audio_content_type, lang_code
            ),
            timeout=STT_TIMEOUT_SECONDS,
        )

        if not text_query.strip():
            return await self._respond_not_heard(lang_code, detected_lang or "")

        # 2. Context Lookup (Graph-Augmented Vector Search)
        db_data = prefetched_context
        if db_data is None:
            related_artifacts = await graph_augmented_search(text_query)
            if related_artifacts:
                context_parts = []
                for art in related_artifacts:
                    history = art.history_text_vi if lang_code == "vi" else art.history_text_en
                    context_parts.append(f"[{art.name_vi} / {art.name_en}]: {history}")
                db_data = "\n\n".join(context_parts)
            elif self._db_lookup:
                db_data = await self._call_db_lookup(text_query, context["db_field"])

        if self._is_unhelpful_context(db_data) and artifact_hint and self._db_lookup:
            db_data = await self._call_db_lookup(artifact_hint, context["db_field"])

        history_context = await self._memory.format_history(session_id or "")
        intent = self._classify_intent(text_query)

        if self._is_unhelpful_context(db_data):
            context_data = (
                self._build_general_chat_context(history_context)
                if intent in ["small_talk", "unknown"]
                else self._build_missing_context(artifact_hint or "", history_context)
            )
        else:
            context_data = self._build_db_context(db_data, history_context, artifact_hint)

        # 3. LLM (non-streaming)
        try:
            if self._llm is None:
                raise RuntimeError("LLM not configured")
            full_response = await asyncio.wait_for(
                self._llm.generate_response(text_query, context_data, lang_code),
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            _LOGGER.exception("Voice LLM step failed")
            full_response = self._llm_fallback_message(
                lang_code, not self._is_unhelpful_context(db_data)
            )

        # 4. Memory update
        if session_id:
            await self._memory.add_turn(session_id, "user", text_query)
            await self._memory.add_turn(session_id, "assistant", full_response)

        # 5. TTS
        audio_out = await self._synthesize_response(full_response, lang_code)

        return VoicePipelineResult(
            audio_bytes=audio_out,
            transcript=text_query,
            response_text=full_response,
            lang=lang_code,
            detected_lang=detected_lang or "",
        )

    async def process_voice_request_stream(
        self,
        audio_bytes: bytes,
        lang_param: str,
        audio_filename: str | None = None,
        audio_content_type: str | None = None,
        session_id: str | None = None,
        artifact_hint: str | None = None,
        prefetched_context: str | None = None,
    ):
        """Process an audio request and yield text chunks followed by final audio."""
        requested_lang = lang_param.strip().lower()
        context = self._language_manager.setup_context(requested_lang)
        lang_code = context["lang_code"]

        if not audio_bytes or len(audio_bytes) < MIN_AUDIO_BYTES:
            res = await self._respond_not_heard(lang_code, "")
            yield {"type": "text", "delta": res.response_text}
            yield {"type": "audio", "audio_bytes": res.audio_bytes, "transcript": "", "response_text": res.response_text}
            return

        # 1. STT
        try:
            if self._stt is None: raise RuntimeError("STT not configured")
            text_query, detected_lang = await self._stt.transcribe(
                audio_bytes, audio_filename, audio_content_type, lang_code
            )
        except Exception as exc:
            yield {"type": "error", "message": f"STT failed: {exc}"}
            return

        if not text_query.strip():
            res = await self._respond_not_heard(lang_code, detected_lang or "")
            yield {"type": "text", "delta": res.response_text}
            yield {"type": "audio", "audio_bytes": res.audio_bytes, "transcript": "", "response_text": res.response_text}
            return

        yield {"type": "transcript", "text": text_query}

        # 2. Context Lookup (Enhanced with Graph-Augmented Vector Search)
        db_data = prefetched_context
        if db_data is None:
            # New Hybrid Search
            related_artifacts = await graph_augmented_search(text_query)
            if related_artifacts:
                # Build context from multiple related artifacts
                context_parts = []
                for art in related_artifacts:
                    history = art.history_text_vi if lang_code == "vi" else art.history_text_en
                    context_parts.append(f"[{art.name_vi} / {art.name_en}]: {history}")
                db_data = "\n\n".join(context_parts)
            elif self._db_lookup:
                # Fallback to old lookup if hybrid search finds nothing
                db_data = await self._call_db_lookup(text_query, context["db_field"])
        
        if self._is_unhelpful_context(db_data) and artifact_hint and self._db_lookup:
            db_data = await self._call_db_lookup(artifact_hint, context["db_field"])

        history_context = await self._memory.format_history(session_id or "")
        intent = self._classify_intent(text_query)
        
        if self._is_unhelpful_context(db_data):
            context_data = self._build_general_chat_context(history_context) if intent in ["small_talk", "unknown"] else self._build_missing_context(artifact_hint or "", history_context)
        else:
            context_data = self._build_db_context(db_data, history_context, artifact_hint)

        # 3. LLM Streaming
        full_response = ""
        try:
            if self._llm is None: raise RuntimeError("LLM not configured")
            async for chunk in self._llm.generate_response_stream(text_query, context_data, lang_code):
                full_response += chunk
                yield {"type": "text", "delta": chunk}
        except Exception as exc:
            full_response = self._llm_fallback_message(lang_code, not self._is_unhelpful_context(db_data))
            yield {"type": "text", "delta": full_response}

        if session_id:
            await self._memory.add_turn(session_id, "user", text_query)
            await self._memory.add_turn(session_id, "assistant", full_response)

        # 4. TTS
        audio_out = await self._synthesize_response(full_response, lang_code)
        yield {
            "type": "audio", 
            "audio_bytes": audio_out, 
            "transcript": text_query, 
            "response_text": full_response,
            "detected_lang": detected_lang
        }

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
