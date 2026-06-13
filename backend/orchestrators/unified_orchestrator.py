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
import hashlib
import logging
import re
import time
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
from utils.prompt_templates import build_voice_system_prompt, build_followup_system_prompt
from utils.rag_debug_logger import log_rag_context
from core.config import get_settings
from core.observability import increment

_LOGGER = logging.getLogger(__name__)

# Timeouts in seconds
STT_TIMEOUT = 20
VISION_TIMEOUT = 25
LLM_TIMEOUT = 18
FOLLOWUP_LLM_TIMEOUT = 12
MIN_AUDIO_BYTES = 800
ANSWER_CACHE_MAX_SIZE = 128
_ANSWER_CACHE: dict[str, str] = {}
_ARTIFACT_INTRO_CACHE: dict[str, str] = {}
_INTRO_CACHE_MAX_SIZE = 64

# Background TTS result cache: token -> {"audio_bytes": bytes, "timestamp": float}
_TTS_RESULT_CACHE: dict[str, dict] = {}
_TTS_RESULT_CACHE_MAX = 32
_TTS_RESULT_TTL = 120  # seconds — auto-expire after 2 minutes

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
    tts_token: Optional[str] = None

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
        llm_skipped = False

        # If artifact_id is not passed, fetch the last active artifact from session memory
        if not recognized_artifact_id and session_id:
            try:
                recent_turns = await self._memory.get_recent_context(session_id, limit=5)
                for turn in reversed(recent_turns):
                    if turn.context_data and "artifact_id" in turn.context_data:
                        val = turn.context_data["artifact_id"]
                        if val:
                            if isinstance(val, (int, str)) and str(val).isdigit():
                                recognized_artifact_id = int(val)
                            else:
                                recognized_artifact_id = val
                            _LOGGER.info("Retrieved active artifact ID from memory: %s", recognized_artifact_id)
                            break
            except Exception as exc:
                _LOGGER.warning("Failed to retrieve active artifact from memory: %s", exc)

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

        # If pre-loaded artifact differs from what the user is asking about in text, override
        if recognized_artifact_id and final_query:
            try:
                query_artifact = await find_artifact_by_name(final_query)
                if query_artifact and str(query_artifact.art_id) != str(recognized_artifact_id):
                    # Classify context intent to determine if it is SWITCH or COMPARE_OR_REFER
                    current_name = recognized_artifact_name or "Địa điểm hiện tại"
                    new_name = self._artifact_name(query_artifact, lang_code)
                    intent = await self._classify_context_intent(
                        current_art_name=current_name,
                        new_art_name=new_name,
                        query=final_query,
                        lang_code=lang_code,
                    )
                    
                    if intent == "SWITCH":
                        previous_id = recognized_artifact_id
                        artifact_info = query_artifact
                        recognized_artifact_id = query_artifact.art_id
                        recognized_artifact_name = self._artifact_name(query_artifact, lang_code)
                        db_context = self._format_artifact_context(query_artifact, lang_code)
                        _LOGGER.info(
                            "Overrode artifact %s with query-matched artifact %s (SWITCH)",
                            previous_id, query_artifact.art_id,
                        )
                    else:
                        # COMPARE_OR_REFER
                        # Retain the current primary location context, but append comparative context
                        primary_context = db_context or ""
                        if not primary_context and artifact_info:
                            primary_context = self._format_artifact_context(artifact_info, lang_code)
                        
                        comp_context = self._format_artifact_context(query_artifact, lang_code)
                        
                        db_context = (
                            f"DB_CONTEXT_PRIMARY ({recognized_artifact_name}):\n{primary_context}\n\n"
                            f"DB_CONTEXT_COMPARATIVE ({new_name}):\n{comp_context}"
                        )
                        _LOGGER.info(
                            "Maintained artifact %s as primary, loaded comparative context for %s (COMPARE_OR_REFER)",
                            recognized_artifact_id, query_artifact.art_id,
                        )
            except Exception as exc:
                _LOGGER.warning("Query-based artifact override failed: %s", exc)

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

        # 4. Prefer cached answers before LLM.
        if artifact_info:
            cached = self._get_cached_answer(artifact_info, final_query, lang_code)
            if cached:
                increment("chat.llm_calls_avoided")
                return await self._finalize_without_tts(
                    cached, final_query, lang_code, session_id, artifact_info,
                    recognized_artifact_id, recognized_artifact_name,
                    detected_lang, "cache", processing_steps,
                )

        small_talk = self._build_small_talk_answer(final_query, lang_code)
        if small_talk:
            increment("chat.llm_calls_avoided")
            return await self._finalize_without_tts(
                small_talk, final_query, lang_code, session_id, artifact_info,
                recognized_artifact_id, recognized_artifact_name,
                detected_lang, "template", processing_steps,
            )

        # 5. Multi-artifact query (no single artifact matched)
        if not artifact_info and final_query:
            multi = await self._find_multi_artifacts(final_query)
            if multi:
                parts = [self._wrapped_summary(art, lang_code) for art in multi]
                combined = "\n\n---\n\n".join(parts)
                increment("chat.llm_calls_avoided")
                return await self._finalize_without_tts(
                    combined, final_query, lang_code, session_id, None,
                    None, None, detected_lang, "db_direct", processing_steps,
                )

        # 6. Prepare LLM Context — classify query to pick prompt & max_tokens
        query_type = self._classify_query_type(final_query, artifact_info)
        _settings = get_settings()
        if query_type == "intro":
            system_prompt = build_voice_system_prompt(lang_code)
            chosen_max_tokens = _settings.LLM_MAX_TOKENS
            chosen_timeout = LLM_TIMEOUT
        else:
            system_prompt = build_followup_system_prompt(lang_code)
            chosen_max_tokens = _settings.LLM_MAX_TOKENS_FOLLOWUP
            chosen_timeout = FOLLOWUP_LLM_TIMEOUT

        history_context = await self._memory.format_history(session_id or "")
        
        # Build a rich prompt context
        llm_context_parts = []
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
        
        # Log RAG context to debug file
        _LOGGER.debug("--- RAG CONTEXT SENT TO LLM ---\n%s\n-------------------------------", llm_full_context)
        log_rag_context(final_query, db_context, answer_source="llm")

        # 7. Generate LLM Response with dynamic max_tokens
        try:
            processing_steps.append(self._step_label("llm", lang_code))
            llm = self._get_llm()
            response_text = await asyncio.wait_for(
                llm.generate_response(
                    final_query, llm_full_context, lang_code,
                    max_tokens=chosen_max_tokens,
                    system_prompt=system_prompt,
                ),
                timeout=chosen_timeout
            )
        except Exception as e:
            _LOGGER.error("LLM generation failed or timed out: %s", e, exc_info=True)
            increment("chat.llm_fallback")
            if artifact_info:
                response_text = self._wrapped_summary(artifact_info, lang_code)
            else:
                response_text = self._build_resilient_fallback_answer(
                    final_query, lang_code, has_database_context
                )
            llm_skipped = True

        if artifact_info and response_text.strip():
            self._set_cached_answer(artifact_info, final_query, lang_code, response_text)

        # 8. Save to Memory
        context_data = {"artifact_id": recognized_artifact_id} if recognized_artifact_id else None
        if session_id:
            if final_query:
                await self._memory.add_turn(session_id, "user", final_query, context_data)
            await self._memory.add_turn(session_id, "assistant", response_text, context_data)

        # 9. Generate Audio Response (TTS) — fire-and-forget background task
        tts_token = None
        if not llm_skipped:
            tts = self._get_tts()
            if tts is not None:
                tts_token = self._make_tts_token(response_text, lang_code)
                # Check if this exact text already has cached audio
                cached_entry = _TTS_RESULT_CACHE.get(tts_token)
                if cached_entry and cached_entry.get("audio_bytes"):
                    _LOGGER.info("TTS cache hit for token %s", tts_token[:12])
                else:
                    processing_steps.append(self._step_label("tts", lang_code))
                    _LOGGER.info(
                        "Launching background TTS synthesis (length=%d, token=%s)",
                        len(response_text), tts_token[:12],
                    )
                    asyncio.create_task(
                        self._background_tts(tts, response_text, lang_code, tts_token)
                    )

        return UnifiedChatResult(
            response_text=response_text,
            audio_bytes=None,  # Always None — frontend polls via tts_token
            transcript=final_query,
            artifact_id=recognized_artifact_id,
            artifact_name=recognized_artifact_name,
            detected_lang=detected_lang,
            answer_source="llm",
            processing_steps=processing_steps,
            artifact_year=artifact_info.year if artifact_info else None,
            artifact_author=artifact_info.author if artifact_info else None,
            artifact_summary=self._short_summary(artifact_info, lang_code) if artifact_info else None,
            tts_token=tts_token,
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
        # Log RAG context to debug file for non-LLM paths
        log_rag_context(
            final_query,
            self._format_artifact_context(artifact_info, lang_code) if artifact_info else "(không có)",
            answer_source=answer_source,
        )
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

    async def _classify_context_intent(
        self, current_art_name: str, new_art_name: str, query: str, lang_code: str
    ) -> str:
        # Prompt phân loại để AI quyết định SWITCH hay COMPARE_OR_REFER
        prompt = (
            f"Bạn là trợ lý AI phân tích ngữ cảnh hội thoại tại Kinh thành Huế.\n"
            f"Địa điểm đang được giới thiệu hiện tại (Current Location): {current_art_name}\n"
            f"Địa điểm mới vừa được nhắc tới trong câu hỏi (New Candidate Location): {new_art_name}\n"
            f"Câu hỏi của người dùng (User Query): \"{query}\"\n\n"
            f"Hãy phân tích xem người dùng đang thực hiện hành động nào sau đây:\n"
            f"1. SWITCH: Người dùng muốn đổi chủ đề hoàn toàn, chuyển sang giới thiệu/kể về/chỉ đường tới địa điểm mới.\n"
            f"   Ví dụ: \"Kể về Ngọ Môn đi\", \"Dẫn tôi tới Điện Kiến Trung\", \"Điện Thái Hòa có gì đẹp?\".\n"
            f"2. COMPARE_OR_REFER: Người dùng đang so sánh, hỏi khoảng cách/hướng đi, hoặc hỏi liên hệ giữa địa điểm hiện tại và địa điểm mới, hoặc câu hỏi vẫn ngụ ý giữ địa điểm hiện tại làm trọng tâm.\n"
            f"   Ví dụ: \"nó với ngọ môn cái nào xây trước?\", \"từ đây đi sang Ngọ Môn như thế nào?\", \"Kiến Trung nằm ở đâu so với Ngọ Môn?\".\n\n"
            f"Hãy trả về kết quả dưới dạng chuỗi chữ hoa duy nhất: \"SWITCH\" hoặc \"COMPARE_OR_REFER\".\n"
            f"Không giải thích gì thêm, chỉ trả về đúng 1 từ khóa."
        )
        # Gọi LLM với max_tokens thấp để trả về nhanh
        llm = self._get_llm()
        response = await llm.generate_response(prompt, context_data="", lang=lang_code, max_tokens=10)
        clean_resp = response.strip().upper()
        if "COMPARE" in clean_resp or "REFER" in clean_resp:
            return "COMPARE_OR_REFER"
        return "SWITCH"

    def _classify_query_type(
        self, query: str, artifact_info: ArtifactInfo | None
    ) -> str:
        """Classify query as 'intro' (needs long response) or 'followup' (shorter response).

        'intro' triggers: marker clicks, first-time introductions, general "tell me about" queries.
        'followup' triggers: specific fact questions (who/when/why), conversational follow-ups.
        """
        normalized = self._normalize_text(query)

        # Marker click → always an intro
        if normalized.startswith("[user sent"):
            return "intro"

        # Explicit intro keywords
        intro_keywords = {
            "gioi thieu", "ke ve", "noi ve", "tim hieu", "thong tin",
            "huong dan vien", "tour guide", "tell me about",
            "describe", "introduce", "information", "what is",
            "short engaging introduction",
        }
        if any(kw in normalized for kw in intro_keywords):
            return "intro"

        # Everything else is a follow-up
        return "followup"

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

        # Safety check: ensure the artifact name appears in the user's query
        # to avoid answering about the wrong artifact (e.g., stale artifact_id)
        artifact_name_normalized = self._normalize_text(artifact.name_vi)
        if artifact_name_normalized and artifact_name_normalized not in normalized:
            # Also check the English name as a fallback
            en_normalized = self._normalize_text(artifact.name_en)
            if not en_normalized or en_normalized not in normalized:
                # Check if at least one significant word from the artifact name is in the query
                art_tokens = [t for t in artifact_name_normalized.split() if len(t) >= 3]
                query_tokens = set(normalized.split())
                if not any(token in query_tokens for token in art_tokens):
                    return None
            
        # Fallback fast-path for common fact queries when LLM is unavailable.
        # Returns a short 1-sentence answer (no _short_summary / full DB text).
        if artifact.year and any(kw in normalized for kw in ("nam", "xay", "built", "year", "when")):
            if lang_code == "vi":
                return f"{artifact.name_vi} được xây dựng vào khoảng năm {artifact.year} dưới triều Nguyễn."
            return f"{artifact.name_en} was built around {artifact.year} during the Nguyen Dynasty."

        if artifact.author and any(kw in normalized for kw in ("ai xay", "tac gia", "author", "who built", "builder")):
            if lang_code == "vi":
                return f"{artifact.name_vi} gắn liền với {artifact.author}."
            return f"{artifact.name_en} is closely tied to {artifact.author}."

        if any(kw in normalized for kw in ("o dau", "dia diem", "where", "location")):
            if lang_code == "vi":
                return f"{artifact.name_vi} nằm trong khu vực Đại Nội Huế."
            return f"{artifact.name_en} is located within the Hue Imperial City."

        return None

    _GENERAL_KEYWORDS = {
        "gioi thieu", "ke ve", "noi ve", "tim hieu", "thong tin",
        "noi dung", "huong dan vien", "tour guide", "tell me about",
        "describe", "introduce", "about", "information", "what is",
        "y nghia", "meaning", "significance", "tai sao", "why",
        "dung de", "lam gi", "chuc nang", "muc dich", "su dung",
        "use", "used for", "purpose", "function",
        "nam", "xay", "built", "year", "when",
        "ai xay", "tac gia", "author", "who built", "builder",
        "o dau", "dia diem", "where", "location",
        "short engaging introduction",
    }

    async def _build_artifact_description(
        self, artifact: ArtifactInfo, query: str, lang_code: str
    ) -> str | None:
        if artifact is None:
            return None

        normalized = self._normalize_text(query)

        artifact_name_normalized = self._normalize_text(artifact.name_vi)
        if artifact_name_normalized and artifact_name_normalized not in normalized:
            en_normalized = self._normalize_text(artifact.name_en)
            if not en_normalized or en_normalized not in normalized:
                art_tokens = [t for t in artifact_name_normalized.split() if len(t) >= 3]
                query_tokens = set(normalized.split())
                if not any(token in query_tokens for token in art_tokens):
                    return None

        if not any(kw in normalized for kw in self._GENERAL_KEYWORDS):
            return None

        # Map marker click → pre-generated engaging intro, return instantly
        if normalized.startswith("huong dan vien") or normalized.startswith("tour guide"):
            cached_intro = _ARTIFACT_INTRO_CACHE.get(artifact.art_id)
            if cached_intro:
                return cached_intro
            try:
                intro = await self._generate_intro(artifact, lang_code)
                if len(_ARTIFACT_INTRO_CACHE) >= _INTRO_CACHE_MAX_SIZE:
                    _ARTIFACT_INTRO_CACHE.pop(next(iter(_ARTIFACT_INTRO_CACHE)))
                _ARTIFACT_INTRO_CACHE[artifact.art_id] = intro
                return intro
            except Exception as e:
                _LOGGER.warning("Intro generation failed for %s: %s", artifact.art_id, e)
                return self._wrapped_summary(artifact, lang_code)

        # Regular chat query → per-query cache + LLM with user's exact question
        cached = self._get_cached_answer(artifact, query, lang_code)
        if cached:
            return cached

        try:
            llm = self._get_llm()
            _settings = get_settings()
            context = self._format_artifact_context(artifact, lang_code)
            # Follow-up questions use shorter prompt & fewer tokens
            system_prompt = build_followup_system_prompt(lang_code)
            full_context = f"DB_CONTEXT:\n{context}"

            answer = await asyncio.wait_for(
                llm.generate_response(
                    query, full_context, lang_code,
                    max_tokens=_settings.LLM_MAX_TOKENS_FOLLOWUP,
                    system_prompt=system_prompt,
                ),
                timeout=FOLLOWUP_LLM_TIMEOUT,
            )

            self._set_cached_answer(artifact, query, lang_code, answer)
            return answer
        except Exception as e:
            _LOGGER.warning("LLM answer failed for %s query '%s': %s", artifact.art_id, query[:60], e)
            return self._wrapped_summary(artifact, lang_code)

    async def _generate_intro(self, artifact: ArtifactInfo, lang_code: str) -> str:
        llm = self._get_llm()
        _settings = get_settings()
        context = self._format_artifact_context(artifact, lang_code)
        system_prompt = build_voice_system_prompt(lang_code)  # Full intro prompt

        if lang_code == "vi":
            prompt = f"Hãy giới thiệu chi tiết và hấp dẫn về {self._artifact_name(artifact, lang_code)} cho vị khách quý"
        else:
            prompt = f"Give a detailed, engaging introduction to {self._artifact_name(artifact, lang_code)} for our honored guest"

        full_context = f"DB_CONTEXT:\n{context}"

        intro = await asyncio.wait_for(
            llm.generate_response(
                prompt, full_context, lang_code,
                max_tokens=_settings.LLM_MAX_TOKENS,  # Full tokens for intro
                system_prompt=system_prompt,
            ),
            timeout=LLM_TIMEOUT,
        )
        return intro

    def _wrapped_summary(self, artifact: ArtifactInfo, lang_code: str) -> str:
        name = self._artifact_name(artifact, lang_code)
        text = artifact.history_text_vi if lang_code == "vi" else artifact.history_text_en
        text = (text or "").strip()
        if not text:
            return f"{name}: (chưa có dữ liệu)" if lang_code == "vi" else f"{name}: (no data available)"
        if lang_code == "vi":
            return (
                f"Chào bạn! Hãy cùng tôi khám phá {name} - một địa điểm lịch sử đặc biệt trong khu vực Hoàng thành Huế.\n\n"
                f"{text}\n\n"
                f"Hy vọng những thông tin trên sẽ giúp bạn hiểu thêm về giá trị lịch sử của nơi này. "
                f"Nếu bạn muốn tìm hiểu thêm về năm xây dựng, tác giả hay ý nghĩa của {name}, đừng ngần ngại hỏi tôi nhé!"
            )
        return (
            f"Hello! Let me introduce you to {name} - a special historical site within the Hue Imperial City.\n\n"
            f"{text}\n\n"
            f"I hope this information helps you better understand the historical value of this place. "
            f"If you'd like to know more about its construction year, author, or significance, feel free to ask!"
        )

    async def _find_multi_artifacts(self, query: str) -> list[ArtifactInfo]:
        normalized = self._normalize_text(query)
        for sep in (" va ", " and ", " & "):
            if sep in normalized:
                parts = [p.strip() for p in normalized.split(sep) if p.strip()]
                artifacts = []
                for part in parts:
                    art = await find_artifact_by_name(part)
                    if art:
                        artifacts.append(art)
                if len(artifacts) >= 2:
                    return artifacts
        return []

    def _build_small_talk_answer(self, query: str, lang_code: str) -> str | None:
        normalized = self._normalize_text(query)
        greetings = {"xin chao", "chao", "hello", "hi", "hey"}
        thanks = {"cam on", "thank", "thanks"}
        if normalized in greetings or any(normalized.startswith(item) for item in greetings):
            if lang_code == "vi":
                return (
                    "Kính chào khanh! Ta là một vị quan uyên bác trong triều đình nhà Nguyễn, "
                    "sẵn lòng dẫn khanh tham quan Kinh thành Huế. "
                    "Khanh có thể gửi ảnh di tích, chụp bằng webcam hoặc hỏi ta về bất kỳ địa điểm lịch sử nào."
                )
            return (
                "Greetings, honored guest! I am a scholarly official of the Nguyen Dynasty court, "
                "ready to guide you through the Hue Imperial City. "
                "You may send a photo of an artifact, use the webcam, or ask me about any historical site."
            )
        if any(item in normalized for item in thanks):
            if lang_code == "vi":
                return "Ta rất vui khi được phụng sự khanh trong chuyến tham quan này."
            return "It is my honor to serve you on this tour, dear guest."
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
            "",
            "=== FULL DETAILED DESCRIPTION (use ALL of this in your response) ===",
            history,
        ]
        return "\n".join(facts)

    @staticmethod
    def _artifact_name(artifact: ArtifactInfo, lang_code: str) -> str:
        return artifact.name_vi if lang_code == "vi" else artifact.name_en

    @staticmethod
    def _short_summary(artifact: ArtifactInfo, lang_code: str) -> str:
        text = artifact.history_text_vi if lang_code == "vi" else artifact.history_text_en
        sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
        summary = " ".join(sentence for sentence in sentences[:15] if sentence).strip()
        return summary or text[:800].strip()

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        if not text:
            return ""
        text_cleaned = text.replace("đ", "d").replace("Đ", "d")
        normalized = unicodedata.normalize("NFD", text_cleaned)
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

    # ── Background TTS helpers ───────────────────────────────────────────

    @staticmethod
    def _make_tts_token(text: str, lang: str) -> str:
        """Deterministic hash so identical text reuses the same cache slot."""
        digest = hashlib.sha256(f"{lang}:{text}".encode("utf-8")).hexdigest()
        return digest[:24]

    @staticmethod
    async def _background_tts(
        tts: BaseTTS, text: str, lang: str, token: str
    ) -> None:
        """Synthesize TTS in the background and store the result in cache."""
        try:
            audio = await asyncio.wait_for(
                tts.synthesize(text, lang),
                timeout=30,
            )
            if audio:
                _evict_tts_cache()
                _TTS_RESULT_CACHE[token] = {
                    "audio_bytes": audio,
                    "timestamp": time.time(),
                }
                _LOGGER.info("Background TTS completed for token %s (%d bytes)", token[:12], len(audio))
            else:
                _LOGGER.info("Background TTS returned empty audio for token %s", token[:12])
        except Exception as exc:
            _LOGGER.warning("Background TTS failed for token %s: %s", token[:12], exc)

    @staticmethod
    def fetch_tts_audio(token: str) -> bytes | None:
        """Retrieve synthesized audio by token. Returns None if not ready."""
        entry = _TTS_RESULT_CACHE.get(token)
        if not entry:
            return None
        # Expire stale entries
        if time.time() - entry["timestamp"] > _TTS_RESULT_TTL:
            _TTS_RESULT_CACHE.pop(token, None)
            return None
        return entry.get("audio_bytes")


def _evict_tts_cache() -> None:
    """Evict oldest entries if cache exceeds max size, and remove expired."""
    now = time.time()
    # Remove expired first
    expired = [k for k, v in _TTS_RESULT_CACHE.items() if now - v["timestamp"] > _TTS_RESULT_TTL]
    for k in expired:
        _TTS_RESULT_CACHE.pop(k, None)
    # Evict oldest if still over limit
    while len(_TTS_RESULT_CACHE) >= _TTS_RESULT_CACHE_MAX:
        oldest_key = next(iter(_TTS_RESULT_CACHE))
        _TTS_RESULT_CACHE.pop(oldest_key, None)
