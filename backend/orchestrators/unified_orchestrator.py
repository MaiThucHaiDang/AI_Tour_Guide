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
import json
from dataclasses import dataclass, field
from time import perf_counter
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
    hybrid_multi_source_search,
)
from schemas.vision import ArtifactInfo
from utils.prompt_templates import build_voice_system_prompt
from core.observability import increment

_LOGGER = logging.getLogger(__name__)

# Timeouts in seconds
STT_TIMEOUT = 20
VISION_TIMEOUT = 25
LLM_TIMEOUT = 30
TTS_TIMEOUT = 20
QUERY_PARSE_TIMEOUT = 8
MIN_AUDIO_BYTES = 800
ANSWER_CACHE_MAX_SIZE = 128
_ANSWER_CACHE: dict[str, str] = {}

# Vietnamese pronouns that indicate follow-up questions
_FOLLOWUP_PRONOUNS = {"nó", "chỗ này", "ở đó", "đó", "đây", "nơi này", "nơi đó", "chỗ đó"}

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

        # Pre-load only target metadata if artifact_id is provided, do not force-pin context yet
        if recognized_artifact_id:
            try:
                artifact_info = await get_artifact_by_id(recognized_artifact_id)
                if artifact_info:
                    recognized_artifact_name = self._artifact_name(artifact_info, lang_code)
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

        history_context = await self._memory.format_history(session_id or "")

        # ─── Query Understanding (Parser) ───
        parsed_query = {
            "intent": "other",
            "entities": [],
            "question_type": "unknown",
            "needs_artifact_context": False,
            "needs_event_context": False,
            "resolved_subject": None
        }

        if final_query.strip():
            # Step A: Run rule-based parser first (fast, local, 0 tokens)
            parsed_query = self._rule_based_parse(final_query)
            
            # Step B: Also detect follow-up pronoun if intent was 'other'
            if (
                parsed_query.get("intent") == "other"
                and session_id
                and any(p in final_query.lower() for p in _FOLLOWUP_PRONOUNS)
            ):
                parsed_query["intent"] = "follow_up"

            # Step C: Try to resolve follow-up from memory
            if (
                parsed_query.get("intent") == "follow_up"
                and not parsed_query.get("resolved_subject")
                and session_id
            ):
                try:
                    recent_turns = await self._memory.get_recent_context(session_id, limit=4)
                    for turn in reversed(recent_turns):
                        if turn.context_data and turn.context_data.get("artifact_id"):
                            fallback_art = await get_artifact_by_id(str(turn.context_data["artifact_id"]))
                            if fallback_art:
                                parsed_query["resolved_subject"] = self._artifact_name(fallback_art, lang_code)
                                recognized_artifact_id = turn.context_data["artifact_id"]
                                artifact_info = fallback_art
                                recognized_artifact_name = self._artifact_name(fallback_art, lang_code)
                                _LOGGER.info("Follow-up resolved from memory (pre-LLM): %s (ID: %s)", recognized_artifact_name, recognized_artifact_id)
                                break
                except Exception as e:
                    _LOGGER.warning("Follow-up memory resolution failed (pre-LLM): %s", e)

            # Step D: Check if we still need the LLM parser
            needs_llm_parse = False
            if parsed_query.get("intent") == "other":
                needs_llm_parse = True
            elif parsed_query.get("intent") == "follow_up" and not parsed_query.get("resolved_subject"):
                # Follow-up pronoun detected but memory resolution found nothing, fallback to LLM
                needs_llm_parse = True

            if needs_llm_parse:
                parse_start = perf_counter()
                try:
                    processing_steps.append(self._step_label("query_parse", lang_code))
                    parsed_query = await asyncio.wait_for(
                        self._parse_query(final_query, history_context),
                        timeout=QUERY_PARSE_TIMEOUT,
                    )
                    _LOGGER.info("Structured Query Parser output: %s (%.1fs)", parsed_query, perf_counter() - parse_start)
                except asyncio.TimeoutError:
                    _LOGGER.warning("Query parsing timed out after %ss, using rule-based fallback", QUERY_PARSE_TIMEOUT)
                except Exception as e:
                    _LOGGER.error("Query parsing failed: %s, using rule-based fallback", e)
            else:
                _LOGGER.info("Skipped LLM query parsing, using resolved query context: %s", parsed_query)


        # ─── Randomized Pre-generated Introduction Gating ───
        is_intro_query = (
            parsed_query.get("intent") == "introduce"
            or "giới thiệu ngắn gọn và hấp dẫn về" in final_query.lower()
            or "give a short, engaging introduction to" in final_query.lower()
        )

        if is_intro_query:
            target_id = recognized_artifact_id
            if not target_id:
                search_term = ""
                if parsed_query.get("entities"):
                    search_term = parsed_query["entities"][0]
                elif parsed_query.get("resolved_subject"):
                    search_term = parsed_query["resolved_subject"]
                else:
                    cleaned_query = final_query
                    for prefix in [
                        "hướng dẫn viên: giới thiệu ngắn gọn và hấp dẫn về",
                        "tour guide: give a short, engaging introduction to",
                        "giới thiệu về", "introduce"
                    ]:
                        if cleaned_query.lower().startswith(prefix):
                            cleaned_query = cleaned_query[len(prefix):].strip()
                    search_term = cleaned_query
                
                if search_term:
                    try:
                        art_info = await find_artifact_by_name(search_term)
                        if art_info:
                            target_id = int(art_info.art_id)
                            artifact_info = art_info
                            recognized_artifact_id = art_info.art_id
                            recognized_artifact_name = self._artifact_name(art_info, lang_code)
                    except Exception:
                        pass

            if target_id:
                from services.voice.intro_service import intro_service
                cached_intro = intro_service.get_random_intro(int(target_id), lang_code)
                if cached_intro:
                    _LOGGER.info("Returning randomized pre-generated introduction from cache for ID: %d", int(target_id))
                    if not artifact_info:
                        try:
                            artifact_info = await get_artifact_by_id(str(target_id))
                        except Exception:
                            pass
                    return await self._finalize_without_tts(
                        cached_intro, final_query, lang_code, session_id, artifact_info,
                        str(target_id), recognized_artifact_name,
                        detected_lang, "cache", processing_steps
                    )

        # ─── Direct Context Loading (Bypass Hybrid Search & Embedding API if ID is known) ───
        if recognized_artifact_id and not db_context:
            if not artifact_info:
                try:
                    artifact_info = await get_artifact_by_id(recognized_artifact_id)
                except Exception as exc:
                    _LOGGER.warning("Direct context lookup failed: %s", exc)
            
            if artifact_info:
                db_context = self._format_artifact_context(artifact_info, lang_code)
                recognized_artifact_name = self._artifact_name(artifact_info, lang_code)
                # Fetch related facts locally from Database without vector search
                try:
                    from core.database import async_session_factory
                    from models.graph import KnowledgeFact
                    from sqlalchemy import select
                    async with async_session_factory() as session:
                        fact_stmt = select(KnowledgeFact).where(KnowledgeFact.artifact_id == int(recognized_artifact_id)).limit(5)
                        fact_res = await session.execute(fact_stmt)
                        facts = fact_res.scalars().all()
                        if facts:
                            db_context += "\n\n[DỮ KIỆN LỊCH SỬ LIÊN QUAN / HISTORICAL FACTS]\n" + "\n".join(f"- {f.fact_text}" for f in facts)
                except Exception as e:
                    _LOGGER.warning("Failed to fetch facts for direct context: %s", e)
                
                confidence_score = 0.95
                _LOGGER.info("Loaded direct context for artifact ID: %s without embedding call", recognized_artifact_id)

        # ─── Dynamic Hybrid Multi-Source Retrieval & Gating ───
        confidence_score = 0.95 if db_context else 0.5
        retrieved_data = None
        
        search_query = final_query
        # ─── Query Rewriting (Coreference Resolution) for Follow-up questions ───
        if parsed_query.get("intent") == "follow_up" and parsed_query.get("resolved_subject"):
            subject = parsed_query["resolved_subject"]
            replaced = False
            for p in _FOLLOWUP_PRONOUNS:
                pattern = r'\b' + re.escape(p) + r'\b'
                if re.search(pattern, search_query, re.IGNORECASE):
                    search_query = re.sub(pattern, subject, search_query, flags=re.IGNORECASE)
                    replaced = True
            if not replaced:
                # If no pronoun matches directly in text, prepend the resolved subject to query
                search_query = f"{subject} {final_query}"
            _LOGGER.info("Query rewritten for RAG search: %s -> %s", final_query, search_query)
        # Note: If not follow-up, we keep the original full user query (search_query = final_query)
        # to preserve full natural language semantic details for Vector Search on FAQ,
        # rather than discarding all words except the entity name.

        if not db_context and parsed_query.get("intent") not in ("small_talk", "out_of_scope") and search_query.strip():
            retrieval_start = perf_counter()
            try:
                processing_steps.append(self._step_label("retrieval", lang_code))
                retrieved_data = await hybrid_multi_source_search(search_query, lang_code)
                _LOGGER.info("Hybrid retrieval completed in %.1fs", perf_counter() - retrieval_start)
                
                db_context = retrieved_data.get("context_text", "")
                best_score = retrieved_data.get("best_score", 0.0)
                
                if retrieved_data.get("matched_artifacts") or retrieved_data.get("matched_locations"):
                    if best_score >= 0.85:
                        confidence_score = 0.95
                    elif best_score >= 0.5:
                        confidence_score = 0.70
                    else:
                        confidence_score = 0.50
                elif retrieved_data.get("matched_facts") or retrieved_data.get("matched_faqs"):
                    confidence_score = 0.60
                else:
                    confidence_score = 0.20
                
                if retrieved_data.get("matched_artifacts"):
                    first_art = retrieved_data["matched_artifacts"][0]
                    artifact_info = first_art
                    recognized_artifact_id = str(first_art.art_id)
                    recognized_artifact_name = self._artifact_name(first_art, lang_code)
            except Exception as e:
                _LOGGER.error("Hybrid retrieval failed (%.1fs): %s", perf_counter() - retrieval_start, e, exc_info=True)
                confidence_score = 0.20

        if parsed_query.get("intent") == "out_of_scope":
            confidence_score = 0.10

        if not db_context and artifact_id:
            try:
                artifact_info = await get_artifact_by_id(str(artifact_id))
                if artifact_info:
                    db_context = self._format_artifact_context(artifact_info, lang_code)
                    recognized_artifact_id = str(artifact_id)
                    recognized_artifact_name = self._artifact_name(artifact_info, lang_code)
                    confidence_score = 0.85
                    _LOGGER.info("Fallback loaded pinned context for ID: %s", artifact_id)
            except Exception as exc:
                _LOGGER.warning("Fallback pre-load failed: %s", exc)

        if db_context and not retrieved_data:
            confidence_score = 0.95

        # 4. Prefer cheap answers before LLM (Cache and small talk only, no direct build fast-paths)
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

        # 5. Prepare LLM Context & Confidence Gating Instruction
        if confidence_score >= 0.8:
            confidence_label = "HIGH"
        elif confidence_score >= 0.4:
            confidence_label = "MEDIUM"
        else:
            confidence_label = "LOW"

        confidence_instructions = ""
        if lang_code == "vi":
            if confidence_label == "HIGH":
                confidence_instructions = (
                    "CONFIDENCE_LEVEL: HIGH\n"
                    "Hướng dẫn trả lời: Bạn có thông tin rất chính xác và đầy đủ trong DB_CONTEXT. Hãy trả lời câu hỏi trực tiếp, chi tiết và sinh động dựa trên DB_CONTEXT."
                )
            elif confidence_label == "MEDIUM":
                confidence_instructions = (
                    "CONFIDENCE_LEVEL: MEDIUM\n"
                    "Hướng dẫn trả lời: Thông tin trong DB_CONTEXT chỉ khớp bán phần. Hãy bắt đầu câu trả lời bằng cụm từ: 'Dạ, theo tài liệu lịch sử hiện có về Đại Nội...' hoặc 'Theo ghi chép hiện tại...' và trả lời dựa trên DB_CONTEXT, không tự ý suy đoán các chi tiết lịch sử."
                )
            else:
                confidence_instructions = (
                    "CONFIDENCE_LEVEL: LOW (OR OUT OF SCOPE)\n"
                    "Hướng dẫn trả lời: KHÔNG được tự ý bịa đặt thông tin lịch sử, nhân vật, ngày tháng. Hãy lịch sự phản hồi rằng: 'Dạ, hiện tại dữ liệu thuyết minh của Đại Nội Huế chưa có thông tin chi tiết về nội dung bạn hỏi. Bạn có muốn hỏi về các địa danh nổi tiếng khác như Ngọ Môn, Điện Thái Hòa hay Thế Miếu không?'"
                )
        else:
            if confidence_label == "HIGH":
                confidence_instructions = (
                    "CONFIDENCE_LEVEL: HIGH\n"
                    "Guidance: You have accurate information in DB_CONTEXT. Answer the question directly and dynamically based on DB_CONTEXT."
                )
            elif confidence_label == "MEDIUM":
                confidence_instructions = (
                    "CONFIDENCE_LEVEL: MEDIUM\n"
                    "Guidance: The info in DB_CONTEXT is a partial match. Begin your answer with 'According to available historical records of the Citadel...' and answer based on DB_CONTEXT without guessing details."
                )
            else:
                confidence_instructions = (
                    "CONFIDENCE_LEVEL: LOW (OR OUT OF SCOPE)\n"
                    "Guidance: Do NOT invent historical details. Politely respond: 'I apologize, but my current guide records do not contain detailed information about this subject. Would you like to ask about other prominent landmarks like Ngo Mon Gate, Thai Palace, or The Mieu instead?'"
                )

        is_voice_chat = bool(audio_bytes and len(audio_bytes) >= MIN_AUDIO_BYTES)
        if is_voice_chat:
            system_prompt = build_voice_system_prompt(lang_code)
        else:
            from utils.prompt_templates import build_text_system_prompt
            system_prompt = build_text_system_prompt(lang_code)
        
        # Build a rich prompt context
        llm_context_parts = [system_prompt, confidence_instructions]
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
        llm_start = perf_counter()
        try:
            processing_steps.append(self._step_label("llm", lang_code))
            llm = self._get_llm()
            response_text = await asyncio.wait_for(
                llm.generate_response(
                    final_query, llm_full_context, lang_code
                ),
                timeout=LLM_TIMEOUT
            )
            _LOGGER.info("LLM response generated in %.1fs (confidence=%s, has_db_ctx=%s)", perf_counter() - llm_start, confidence_label, has_database_context)
        except asyncio.TimeoutError:
            _LOGGER.error("LLM generation TIMED OUT after %.1fs (timeout=%ss, confidence=%s, has_db_ctx=%s)", perf_counter() - llm_start, LLM_TIMEOUT, confidence_label, has_database_context)
            increment("chat.llm_fallback")
            direct_ans = None
            if artifact_info:
                try:
                    direct_ans = self._build_direct_answer(artifact_info, final_query, lang_code)
                    if not direct_ans:
                        direct_ans = self._summary_answer(artifact_info, lang_code)
                    if direct_ans:
                        _LOGGER.info("LLM timed out, but successfully generated direct database fallback answer: %s", direct_ans)
                except Exception as dex:
                    _LOGGER.warning("Failed to build direct fallback answer on timeout: %s", dex)
            if direct_ans:
                response_text = direct_ans
            else:
                response_text = self._build_resilient_fallback_answer(
                    final_query, lang_code, has_database_context
                )
        except Exception as e:
            _LOGGER.error("LLM generation failed after %.1fs: %s (confidence=%s, has_db_ctx=%s)", perf_counter() - llm_start, e, confidence_label, has_database_context, exc_info=True)
            increment("chat.llm_fallback")
            direct_ans = None
            if artifact_info:
                try:
                    direct_ans = self._build_direct_answer(artifact_info, final_query, lang_code)
                    if not direct_ans:
                        direct_ans = self._summary_answer(artifact_info, lang_code)
                    if direct_ans:
                        _LOGGER.info("LLM failed, but successfully generated direct database fallback answer: %s", direct_ans)
                except Exception as dex:
                    _LOGGER.warning("Failed to build direct fallback answer on exception: %s", dex)
            if direct_ans:
                response_text = direct_ans
            else:
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

        if any(keyword in normalized for keyword in ("ai xay", "tac gia", "author", "who built", "builder", "ai thiet ke", "thiet ke", "ai lam")):
            if artifact.author:
                if lang_code == "vi":
                    return f"{artifact.name_vi} gắn với {artifact.author}."
                return f"{artifact.name_en} is associated with {artifact.author}."

        if any(keyword in normalized for keyword in ("xay nam", "xay vao", "dung vao", "khi nao", "nam nao", "nam may", "nam bao nhieu", "nien dai", "thoi gian xay", "hoan thanh nam", "vao nam", "built", "year", "when")):
            if artifact.year:
                if lang_code == "vi":
                    return f"{artifact.name_vi} được xây dựng vào khoảng năm {artifact.year}."
                return f"{artifact.name_en} was built around {artifact.year}."

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
        if lang_code == "vi":
            facts = [
                f"Tên di tích: {name}",
                f"Năm xây dựng: {artifact.year or 'Chưa rõ'}",
                f"Tác giả/Triều đại: {artifact.author or 'Chưa rõ'}",
                f"Mã địa điểm: {artifact.loc_id}",
            ]
            return "\n".join(facts) + f"\nTóm tắt lịch sử: {history}"
        else:
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

    def _rule_based_parse(self, query: str) -> dict:
        """Fast rule-based query parser (no LLM call). Used as fallback."""
        q_lower = query.lower()
        intent = "other"
        question_type = "unknown"

        if any(x in q_lower for x in ["giới thiệu", "thuyết minh", "nghe giới thiệu", "introduce"]):
            intent = "introduce"
        elif any(x in q_lower for x in ["xin chào", "chào", "hello", "hi"]):
            intent = "small_talk"
        elif any(p in q_lower for p in _FOLLOWUP_PRONOUNS):
            intent = "follow_up"
        elif any(x in q_lower for x in ["năm nào", "xây năm", "built", "when", "bao giờ"]):
            question_type = "when"
            intent = "ask_artifact_info"
        elif any(x in q_lower for x in ["ở đâu", "where", "vị trí", "location"]):
            question_type = "where"
            intent = "ask_artifact_info"
        elif any(x in q_lower for x in ["ai xây", "who", "tác giả", "author"]):
            question_type = "who"
            intent = "ask_artifact_info"
        elif any(x in q_lower for x in ["sự kiện", "lịch sử", "event", "history"]):
            intent = "ask_event_location"

        return {
            "intent": intent,
            "entities": [],
            "question_type": question_type,
            "needs_artifact_context": intent in ("ask_artifact_info", "follow_up", "ask_event_location"),
            "needs_event_context": intent == "ask_event_location",
            "resolved_subject": None
        }

    async def _parse_query(self, query: str, history: str) -> dict:
        """Call LLM to parse query into structured JSON format."""
        llm = self._get_llm()
        prompt = (
            "Bạn là một hệ thống phân tích câu hỏi (Query Understanding) cho ứng dụng Hướng dẫn viên du lịch Đại Nội Huế.\n"
            f"Lịch sử hội thoại trước đó (nếu có):\n{history}\n\n"
            f"Câu hỏi của người dùng: \"{query}\"\n\n"
            "Hãy phân tích câu hỏi trên và trả về kết quả dưới định dạng JSON thuần túy (không dùng markdown codeblock, không thêm bất kỳ văn bản dẫn giải nào khác) theo cấu trúc sau:\n"
            "{\n"
            "  \"intent\": \"ask_artifact_info\" (nếu hỏi về thông tin hiện vật/di tích/địa danh cụ thể) | \"ask_event_location\" (nếu hỏi về sự kiện lịch sử xảy ra ở đâu) | \"small_talk\" (nếu chào hỏi, cảm ơn, xã giao) | \"out_of_scope\" (nếu hỏi ngoài lề không liên quan đến Huế, lịch sử, văn hóa, du lịch) | \"follow_up\" (nếu là câu hỏi nối tiếp có sử dụng đại từ thay thế như 'nó', 'chỗ này', 'ở đó', 'đó' và ám chỉ đối tượng ở lịch sử hội thoại) | \"introduce\" (nếu hỏi yêu cầu giới thiệu về địa điểm) | \"other\",\n"
            "  \"entities\": [mảng các thực thể/tên riêng/tên sự kiện được nhắc đến trong câu hỏi],\n"
            "  \"question_type\": \"what\" | \"when\" | \"where\" | \"who\" | \"why\" | \"how\" | \"unknown\",\n"
            "  \"needs_artifact_context\": true (nếu câu hỏi cần thông tin di tích/hiện vật cụ thể để trả lời) | false,\n"
            "  \"needs_event_context\": true (nếu câu hỏi hỏi về sự kiện lịch sử, nhân vật hoặc sự kiện chung) | false,\n"
            "  \"resolved_subject\": \"Tên di tích/hiện vật cụ thể ở lịch sử hội thoại mà đại từ thay thế ('nó', 'đây', 'đó') đang ám chỉ đến\" | null\n"
            "}\n"
        )
        
        resp = await llm.generate_response(prompt, context_data="", lang="vi")
        clean_resp = resp.strip()
        if clean_resp.startswith("```"):
            lines = clean_resp.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_resp = "\n".join(lines).strip()
            
        try:
            return json.loads(clean_resp)
        except Exception:
            _LOGGER.warning("LLM returned non-JSON for query parser, falling back to rule-based")
            return self._rule_based_parse(query)

    @staticmethod
    def _step_label(step: str, lang_code: str) -> str:
        vi = {
            "stt": "Đã chuyển giọng nói thành văn bản",
            "vision": "Đã nhận diện ảnh",
            "query_parse": "Đã phân tích cấu trúc câu hỏi",
            "retrieval": "Đã truy xuất dữ liệu đa nguồn",
            "llm": "Đã soạn câu trả lời",
            "tts": "Đã tạo audio",
            "cache": "Đã dùng câu trả lời cache",
            "db_direct": "Đã trả lời từ dữ liệu có sẵn",
            "template": "Đã dùng mẫu trả lời nhanh",
        }
        en = {
            "stt": "Transcribed voice to text",
            "vision": "Recognized the image",
            "query_parse": "Analyzed query structure",
            "retrieval": "Retrieved multi-source data",
            "llm": "Prepared the answer",
            "tts": "Generated audio",
            "cache": "Used cached answer",
            "db_direct": "Answered from stored data",
            "template": "Used a quick response template",
        }
        labels = vi if lang_code == "vi" else en
        return labels.get(step, step)
