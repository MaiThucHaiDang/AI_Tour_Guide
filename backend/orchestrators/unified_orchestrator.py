"""Unified orchestrator for handling Text, Voice, and Vision inputs in a single chat flow.

This orchestrator coordinates:
1. STT (Speech-to-Text) if audio is provided.
2. Image Recognition (Vision) if an image is provided.
3. Database Context Retrieval for recognized artifacts.
4. Conversation Memory management.
5. LLM (Large Language Model) response generation.
6. TTS (Text-to-Speech) for the final response.
"""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Optional

from services.ai.interfaces import BaseLLM, BaseSTT, BaseTTS
from services.vision.image_recognition import recognize_image
from services.memory.conversation_memory import ConversationMemory
from utils.language_manager import LanguageManager
from repositories.artifact_repository import (
    canonicalize_transcript_entities,
    find_artifact_by_name,
    get_artifact_by_id,
    get_artifact_context,
    get_artifact_context_by_id,
)
from schemas.vision import ArtifactInfo
from utils.prompt_templates import build_voice_system_prompt
from core.observability import increment

_LOGGER = logging.getLogger(__name__)

# Timeouts in seconds
STT_TIMEOUT = 20
VISION_TIMEOUT = 25
LLM_TIMEOUT = 20
TTS_TIMEOUT = 20
MIN_AUDIO_BYTES = 800
ANSWER_CACHE_MAX_SIZE = 128
_ANSWER_CACHE: dict[str, str] = {}

@dataclass
class UnifiedChatResult:
    response_text: str
    audio_bytes: Optional[bytes] = None
    transcript: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_name: Optional[str] = None
    detected_lang: Optional[str] = None
    answer_source: str = "llm"
    processing_steps: list[str] = field(default_factory=list)
    artifact_year: Optional[int] = None
    artifact_author: Optional[str] = None
    artifact_summary: Optional[str] = None

class UnifiedOrchestrator:
    def __init__(
        self,
        stt: BaseSTT | None,
        llm: BaseLLM | None,
        tts: BaseTTS | None,
        memory: ConversationMemory,
        llm_factory: Callable[[], BaseLLM] | None = None,
        tts_factory: Callable[[], BaseTTS] | None = None,
    ) -> None:
        self._stt = stt
        self._llm = llm
        self._tts = tts
        self._memory = memory
        self._llm_factory = llm_factory
        self._tts_factory = tts_factory
        self._language_manager = LanguageManager()

    async def process_chat_request(
        self,
        text_query: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        image_base64: Optional[str] = None,
        lang: str = "vi",
        session_id: Optional[str] = None,
        audio_filename: Optional[str] = None,
        audio_content_type: Optional[str] = None,
        artifact_id: Optional[int] = None,
    ) -> UnifiedChatResult:
        """Process a multimodal chat request."""
        context = self._language_manager.setup_context(lang)
        lang_code = context["lang_code"]
        
        final_query = text_query or ""
        detected_lang = None
        recognized_artifact_id = artifact_id
        recognized_artifact_name = None
        db_context = ""
        artifact_info: ArtifactInfo | None = None
        processing_steps: list[str] = []

        # Pre-load context if artifact_id is provided
        if recognized_artifact_id:
            try:
                artifact_info = await get_artifact_by_id(recognized_artifact_id)
                if artifact_info:
                    db_context = self._format_artifact_context(artifact_info, lang_code)
                    recognized_artifact_name = self._artifact_name(artifact_info, lang_code)
                    _LOGGER.info("Pre-loaded context for artifact ID: %s", recognized_artifact_id)
            except Exception as exc:
                _LOGGER.warning("Pre-load artifact lookup failed: %s", exc)

        # 1. Start STT and Vision Concurrently
        stt_task = None
        vision_task = None

        if audio_bytes and len(audio_bytes) >= MIN_AUDIO_BYTES:
            if self._stt is None:
                _LOGGER.error("Speech-to-text provider is not configured.")
            else:
                stt_task = asyncio.create_task(
                    self._stt.transcribe(audio_bytes, audio_filename, audio_content_type, lang_code)
                )

        if image_base64:
            vision_task = asyncio.create_task(
                recognize_image(image_base64, lang=lang_code)
            )

        # 2. Await STT and Vision concurrently with proper error handling
        try:
            if stt_task:
                try:
                    processing_steps.append(self._step_label("stt", lang_code))
                    stt_text, det_lang = await asyncio.wait_for(stt_task, timeout=STT_TIMEOUT)
                    if stt_text.strip():
                        final_query = await canonicalize_transcript_entities(stt_text, lang_code)
                        detected_lang = det_lang
                except asyncio.TimeoutError:
                    _LOGGER.error("STT timed out after %s seconds", STT_TIMEOUT)
                    stt_task = None
                except Exception as e:
                    _LOGGER.error("STT failed: %s", e)
                    stt_task = None
        finally:
            # Ensure task is cancelled if not awaited
            if stt_task and not stt_task.done():
                stt_task.cancel()
                try:
                    await stt_task
                except asyncio.CancelledError:
                    pass

        # Handle vision task - ensure it's properly cleaned up
        vision_result = None
        if vision_task:
            try:
                processing_steps.append(self._step_label("vision", lang_code))
                vision_result = await asyncio.wait_for(vision_task, timeout=VISION_TIMEOUT)
            except asyncio.TimeoutError:
                _LOGGER.error("Vision timed out after %s seconds", VISION_TIMEOUT)
                vision_task = None
            except Exception as e:
                _LOGGER.error("Vision processing failed: %s", e)
                vision_task = None
            finally:
                # Ensure task is cancelled if not completed
                if vision_task and not vision_task.done():
                    vision_task.cancel()
                    try:
                        await vision_task
                    except asyncio.CancelledError:
                        pass
        
        if audio_bytes and not final_query.strip() and not image_base64:
            return await self._finalize_without_tts(
                self._not_heard_message(lang_code),
                final_query,
                lang_code,
                session_id,
                artifact_info,
                recognized_artifact_id,
                recognized_artifact_name,
                detected_lang,
                "template",
                processing_steps,
            )

        # 3. Await Vision
        if vision_task:
            try:
                processing_steps.append(self._step_label("vision", lang_code))
                vision_result = await asyncio.wait_for(vision_task, timeout=VISION_TIMEOUT)
                if vision_result.recognized:
                    recognized_artifact_id = vision_result.artifact_id
                    try:
                        artifact_info = await get_artifact_by_id(recognized_artifact_id)
                    except Exception as exc:
                        _LOGGER.warning("Artifact detail lookup failed: %s", exc)
                        artifact_info = None
                    
                    if artifact_info:
                        db_context = self._format_artifact_context(artifact_info, lang_code)
                        recognized_artifact_name = self._artifact_name(artifact_info, lang_code)
                    else:
                        db_context = await get_artifact_context_by_id(
                            recognized_artifact_id, context["db_field"]
                        )
                        recognized_artifact_name = vision_result.raw_label
                    
                    if not final_query:
                        final_query = f"[User sent an image of {recognized_artifact_name}]"
                else:
                    if not final_query:
                        return await self._finalize_without_tts(
                            self._unrecognized_image_message(lang_code),
                            final_query,
                            lang_code,
                            session_id,
                            artifact_info,
                            recognized_artifact_id,
                            recognized_artifact_name,
                            detected_lang,
                            "template",
                            processing_steps,
                        )
                    else:
                        final_query = f"[User sent an unrecognized image. User asks: {final_query}]"
            except Exception as e:
                _LOGGER.error("Vision failed or timed out: %s", e, exc_info=True)

        # 3. If no image but query exists, try searching DB for artifact context (RAG)
        if not db_context and final_query:
            try:
                processing_steps.append(self._step_label("retrieval", lang_code))
                artifact_info = await find_artifact_by_name(final_query)
                if artifact_info:
                    recognized_artifact_id = artifact_info.art_id
                    recognized_artifact_name = self._artifact_name(artifact_info, lang_code)
                    db_context = self._format_artifact_context(artifact_info, lang_code)
                else:
                    db_context = await get_artifact_context(final_query, context["db_field"])
            except Exception as e:
                _LOGGER.error("DB context lookup failed: %s", e, exc_info=True)

        # 4. Prefer cheap answers before LLM.
        if artifact_info:
            cached = self._get_cached_answer(artifact_info, final_query, lang_code)
            if cached:
                increment("chat.llm_calls_avoided")
                return await self._finalize_without_tts(
                    cached, final_query, lang_code, session_id, artifact_info,
                    recognized_artifact_id, recognized_artifact_name,
                    detected_lang, "cache", processing_steps,
                )

            direct_answer = self._build_direct_answer(artifact_info, final_query, lang_code)
            if direct_answer:
                self._set_cached_answer(artifact_info, final_query, lang_code, direct_answer)
                increment("chat.llm_calls_avoided")
                return await self._finalize_without_tts(
                    direct_answer, final_query, lang_code, session_id, artifact_info,
                    recognized_artifact_id, recognized_artifact_name,
                    detected_lang, "db_direct", processing_steps,
                )

        small_talk = self._build_small_talk_answer(final_query, lang_code)
        if small_talk:
            increment("chat.llm_calls_avoided")
            return await self._finalize_without_tts(
                small_talk, final_query, lang_code, session_id, artifact_info,
                recognized_artifact_id, recognized_artifact_name,
                detected_lang, "template", processing_steps,
            )

        # 5. Prepare LLM Context
        history_context = await self._memory.format_history(session_id or "")
        system_prompt = build_voice_system_prompt(lang_code)
        
        # Build a rich prompt context
        llm_context_parts = [system_prompt]
        if history_context:
            llm_context_parts.append(f"CONVERSATION_HISTORY:\n{history_context}")
        
        has_database_context = bool(
            db_context
            and "No matching artifact" not in db_context
            and "Database is temporarily unavailable" not in db_context
        )

        if has_database_context:
            llm_context_parts.append(f"DB_CONTEXT:\n{db_context}")
        else:
            increment("chat.no_database_context")
            llm_context_parts.append(self._build_general_context(final_query, history_context, lang_code))

        llm_full_context = "\n\n".join(llm_context_parts)
        
        # Log the full context sent to the LLM for debugging RAG data
        _LOGGER.debug("--- RAG CONTEXT SENT TO LLM ---\n%s\n-------------------------------", llm_full_context)

        # 6. Generate LLM Response
        try:
            processing_steps.append(self._step_label("llm", lang_code))
            llm = self._get_llm()
            response_text = await asyncio.wait_for(
                llm.generate_response(
                    final_query, llm_full_context, lang_code
                ),
                timeout=LLM_TIMEOUT
            )
        except Exception as e:
            _LOGGER.error("LLM generation failed or timed out: %s", e, exc_info=True)
            increment("chat.llm_fallback")
            response_text = self._build_resilient_fallback_answer(
                final_query, lang_code, has_database_context
            )

        if artifact_info and response_text.strip():
            self._set_cached_answer(artifact_info, final_query, lang_code, response_text)

        # 7. Save to Memory
        context_data = {"artifact_id": recognized_artifact_id} if recognized_artifact_id else None
        if session_id:
            if final_query:
                await self._memory.add_turn(session_id, "user", final_query, context_data)
            await self._memory.add_turn(session_id, "assistant", response_text, context_data)

        # 8. Generate Audio Response (TTS)
        synthesized_audio = None
        try:
            tts = self._get_tts()
            if tts is not None:
                processing_steps.append(self._step_label("tts", lang_code))
                synthesized_audio = await asyncio.wait_for(
                    tts.synthesize(response_text, lang_code),
                    timeout=TTS_TIMEOUT
                )
        except Exception as e:
            _LOGGER.error("TTS failed or timed out: %s", e, exc_info=True)

        return UnifiedChatResult(
            response_text=response_text,
            audio_bytes=synthesized_audio,
            transcript=final_query,
            artifact_id=recognized_artifact_id,
            artifact_name=recognized_artifact_name,
            detected_lang=detected_lang,
            answer_source="llm",
            processing_steps=processing_steps,
            artifact_year=artifact_info.year if artifact_info else None,
            artifact_author=artifact_info.author if artifact_info else None,
            artifact_summary=self._short_summary(artifact_info, lang_code) if artifact_info else None,
        )

    async def _finalize_without_tts(
        self,
        response_text: str,
        final_query: str,
        lang_code: str,
        session_id: str | None,
        artifact_info: ArtifactInfo | None,
        artifact_id: str | None,
        artifact_name: str | None,
        detected_lang: str | None,
        answer_source: str,
        processing_steps: list[str],
    ) -> UnifiedChatResult:
        context_data = {"artifact_id": artifact_id} if artifact_id else None
        if session_id:
            if final_query:
                await self._memory.add_turn(session_id, "user", final_query, context_data)
            await self._memory.add_turn(session_id, "assistant", response_text, context_data)
        return UnifiedChatResult(
            response_text=response_text,
            audio_bytes=None,
            transcript=final_query,
            artifact_id=artifact_id,
            artifact_name=artifact_name,
            detected_lang=detected_lang,
            answer_source=answer_source,
            processing_steps=processing_steps + [self._step_label(answer_source, lang_code)],
            artifact_year=artifact_info.year if artifact_info else None,
            artifact_author=artifact_info.author if artifact_info else None,
            artifact_summary=self._short_summary(artifact_info, lang_code) if artifact_info else None,
        )

    def _get_llm(self) -> BaseLLM:
        if self._llm is None:
            if self._llm_factory is None:
                raise RuntimeError("LLM provider is not configured.")
            self._llm = self._llm_factory()
        return self._llm

    def _get_tts(self) -> BaseTTS | None:
        if self._tts is None and self._tts_factory is not None:
            self._tts = self._tts_factory()
        return self._tts

    def _build_direct_answer(
        self, artifact: ArtifactInfo, query: str, lang_code: str
    ) -> str | None:
        normalized = self._normalize_text(query)
        
        # Never use the fast-path summary for Locations, let the LLM generate a natural response
        if artifact.art_id and artifact.art_id.startswith("loc_"):
            return None
            
        if not normalized or normalized.startswith("[user sent an image"):
            return self._summary_answer(artifact, lang_code)

        if any(keyword in normalized for keyword in ("nam", "xay", "built", "year", "when")):
            if artifact.year:
                if lang_code == "vi":
                    return f"{artifact.name_vi} được xây dựng vào khoảng năm {artifact.year}."
                return f"{artifact.name_en} was built around {artifact.year}."

        if any(keyword in normalized for keyword in ("ai xay", "tac gia", "author", "who built", "builder")):
            if artifact.author:
                if lang_code == "vi":
                    return f"{artifact.name_vi} gắn với {artifact.author}."
                return f"{artifact.name_en} is associated with {artifact.author}."

        if any(keyword in normalized for keyword in ("o dau", "dia diem", "where", "location")):
            if lang_code == "vi":
                return f"{artifact.name_vi} thuộc mã địa điểm {artifact.loc_id}. Bạn có thể xem chi tiết địa điểm ở bảng thông tin bên phải."
            return f"{artifact.name_en} belongs to location ID {artifact.loc_id}. You can review the location details in the side panel."

        # Let the LLM handle storytelling for maximum engagement
        if any(keyword in normalized for keyword in ("tom tat", "gioi thieu", "ke ngan", "y nghia", "meaning", "summary", "describe", "what is")):
            return self._summary_answer(artifact, lang_code)

        return None

    def _summary_answer(self, artifact: ArtifactInfo, lang_code: str) -> str:
        name = self._artifact_name(artifact, lang_code)
        summary = self._short_summary(artifact, lang_code)
        if lang_code == "vi":
            return f"{name}: {summary}"
        return f"{name}: {summary}"

    def _build_small_talk_answer(self, query: str, lang_code: str) -> str | None:
        normalized = self._normalize_text(query)
        greetings = {"xin chao", "chao", "hello", "hi", "hey"}
        thanks = {"cam on", "thank", "thanks"}
        if normalized in greetings or any(normalized.startswith(item) for item in greetings):
            if lang_code == "vi":
                return "Xin chào! Bạn có thể tải ảnh hiện vật, chụp bằng webcam hoặc hỏi trực tiếp về một địa điểm lịch sử."
            return "Hello! You can upload an artifact photo, use the webcam, or ask about a historical site."
        if any(item in normalized for item in thanks):
            return "Rất vui được hỗ trợ bạn." if lang_code == "vi" else "Happy to help."
        return None

    @staticmethod
    def _build_general_context(query: str, history_context: str, lang_code: str) -> str:
        if lang_code == "vi":
            guide = (
                "GENERAL_CHAT:\n"
                "Không tìm thấy hiện vật khớp trong dữ liệu nội bộ cho câu hỏi này. "
                "Hãy vẫn trả lời như một hướng dẫn viên du lịch nếu câu hỏi thuộc văn hóa, "
                "lịch sử, địa điểm tham quan, trải nghiệm du lịch hoặc cách sử dụng ứng dụng. "
                "Nếu câu hỏi hỏi về một hiện vật cụ thể mà bạn không chắc, hãy nói rõ rằng "
                "dữ liệu hiện có chưa có mục đó, rồi đưa ra hướng xử lý: gửi ảnh rõ hơn, "
                "nêu tên hiện vật, hoặc hỏi về địa điểm liên quan. Không bịa ngày tháng, tác giả "
                "hoặc chi tiết lịch sử cụ thể. Trả lời ngắn, tự nhiên, hữu ích."
            )
        else:
            guide = (
                "GENERAL_CHAT:\n"
                "No matching artifact was found in the internal collection for this question. "
                "Still answer as a tour guide when the question is about culture, history, "
                "destinations, travel experience, or how to use the app. If the visitor asks "
                "about a specific artifact and you are not sure, say that the current collection "
                "does not include it yet, then suggest sending a clearer photo, naming the artifact, "
                "or asking about a related destination. Do not invent dates, authors, or specific "
                "historical facts. Keep the answer concise and useful."
            )
        parts = [guide, f"USER_QUESTION:\n{query or '<empty>'}"]
        if history_context:
            parts.append("CONVERSATION_HISTORY:\n" + history_context)
        return "\n\n".join(parts)

    @staticmethod
    def _build_resilient_fallback_answer(
        query: str, lang_code: str, has_database_context: bool
    ) -> str:
        if lang_code == "en":
            if has_database_context:
                return (
                    "I found related information, but I could not prepare the full answer right now. "
                    "Please try again, or ask a shorter question about year, author, location, or meaning."
                )
            return (
                "I do not have a matching item in the current collection for that question yet. "
                "You can send a clearer photo, mention the artifact name, or ask about one of the featured destinations."
            )

        if has_database_context:
            return (
                "Mình đã tìm thấy thông tin liên quan, nhưng chưa soạn được câu trả lời đầy đủ lúc này. "
                "Bạn có thể hỏi ngắn hơn về năm xây dựng, tác giả, vị trí hoặc ý nghĩa lịch sử."
            )
        return (
            "Mình chưa có mục dữ liệu khớp với câu hỏi này trong bộ sưu tập hiện tại. "
            "Bạn có thể gửi ảnh rõ hơn, nêu tên hiện vật, hoặc hỏi về một địa điểm nổi bật trong danh sách."
        )

    @staticmethod
    def _not_heard_message(lang_code: str) -> str:
        if lang_code == "en":
            return "I did not catch that clearly. Please try speaking again or type your question."
        return "Mình chưa nghe rõ. Bạn có thể nói lại chậm hơn hoặc nhập câu hỏi bằng chữ."

    @staticmethod
    def _unrecognized_image_message(lang_code: str) -> str:
        if lang_code == "en":
            return "I couldn't clearly recognize the historical artifact in the image. It might be too blurry, not an artifact, or not in my database yet. Could you take a clearer photo or tell me its name?"
        return "Mình chưa nhận diện được di tích hoặc hiện vật trong ảnh. Có thể ảnh không liên quan, bị mờ hoặc chưa có trong dữ liệu. Bạn có thể chụp rõ hơn hoặc gõ tên của nó cho mình biết nhé!"

    @staticmethod
    def _format_artifact_context(artifact: ArtifactInfo, lang_code: str) -> str:
        name = artifact.name_vi if lang_code == "vi" else artifact.name_en
        history = artifact.history_text_vi if lang_code == "vi" else artifact.history_text_en
        facts = [
            f"Name: {name}",
            f"Year: {artifact.year or 'unknown'}",
            f"Author: {artifact.author or 'unknown'}",
            f"Location ID: {artifact.loc_id}",
        ]
        return "\n".join(facts) + f"\nSummary: {history}"

    @staticmethod
    def _artifact_name(artifact: ArtifactInfo, lang_code: str) -> str:
        return artifact.name_vi if lang_code == "vi" else artifact.name_en

    @staticmethod
    def _short_summary(artifact: ArtifactInfo, lang_code: str) -> str:
        text = artifact.history_text_vi if lang_code == "vi" else artifact.history_text_en
        sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
        summary = " ".join(sentence for sentence in sentences[:2] if sentence).strip()
        return summary or text[:240].strip()

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        normalized = unicodedata.normalize("NFD", text or "")
        stripped = "".join(
            char for char in normalized if unicodedata.category(char) != "Mn"
        )
        cleaned = re.sub(r"[^a-zA-Z0-9\s\[\]]", " ", stripped)
        return " ".join(cleaned.lower().split())

    def _cache_key(self, artifact: ArtifactInfo, query: str, lang_code: str) -> str:
        return f"{lang_code}:{artifact.art_id}:{self._normalize_text(query)}"

    def _get_cached_answer(
        self, artifact: ArtifactInfo, query: str, lang_code: str
    ) -> str | None:
        return _ANSWER_CACHE.get(self._cache_key(artifact, query, lang_code))

    def _set_cached_answer(
        self, artifact: ArtifactInfo, query: str, lang_code: str, answer: str
    ) -> None:
        if len(_ANSWER_CACHE) >= ANSWER_CACHE_MAX_SIZE:
            oldest_key = next(iter(_ANSWER_CACHE))
            _ANSWER_CACHE.pop(oldest_key, None)
        _ANSWER_CACHE[self._cache_key(artifact, query, lang_code)] = answer

    @staticmethod
    def _step_label(step: str, lang_code: str) -> str:
        vi = {
            "stt": "Đã chuyển giọng nói thành văn bản",
            "vision": "Đã nhận diện ảnh",
            "retrieval": "Đã tìm dữ liệu hiện vật",
            "llm": "Đã soạn câu trả lời",
            "tts": "Đã tạo audio",
            "cache": "Đã dùng câu trả lời cache",
            "db_direct": "Đã trả lời từ dữ liệu có sẵn",
            "template": "Đã dùng mẫu trả lời nhanh",
        }
        en = {
            "stt": "Transcribed voice to text",
            "vision": "Recognized the image",
            "retrieval": "Retrieved artifact data",
            "llm": "Prepared the answer",
            "tts": "Generated audio",
            "cache": "Used cached answer",
            "db_direct": "Answered from stored data",
            "template": "Used a quick response template",
        }
        labels = vi if lang_code == "vi" else en
        return labels.get(step, step)
