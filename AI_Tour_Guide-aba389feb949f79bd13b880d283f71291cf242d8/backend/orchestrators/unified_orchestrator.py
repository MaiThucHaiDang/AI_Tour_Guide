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
import base64
from dataclasses import dataclass
from typing import Any, Optional, Callable, Coroutine

from services.ai.interfaces import BaseLLM, BaseSTT, BaseTTS
from services.vision.image_recognition import recognize_image
from services.memory.conversation_memory import ConversationMemory
from utils.language_manager import LanguageManager
from repositories.artifact_repository import get_artifact_context, get_artifact_context_by_id
from utils.prompt_templates import build_voice_system_prompt

_LOGGER = logging.getLogger(__name__)

# Timeouts in seconds
STT_TIMEOUT = 20
VISION_TIMEOUT = 25
LLM_TIMEOUT = 20
TTS_TIMEOUT = 20

@dataclass
class UnifiedChatResult:
    response_text: str
    audio_bytes: Optional[bytes] = None
    transcript: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_name: Optional[str] = None
    detected_lang: Optional[str] = None

class UnifiedOrchestrator:
    def __init__(
        self,
        stt: BaseSTT,
        llm: BaseLLM,
        tts: BaseTTS,
        memory: ConversationMemory,
    ) -> None:
        self._stt = stt
        self._llm = llm
        self._tts = tts
        self._memory = memory
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
    ) -> UnifiedChatResult:
        """Process a multimodal chat request."""
        context = self._language_manager.setup_context(lang)
        lang_code = context["lang_code"]
        
        final_query = text_query or ""
        detected_lang = None
        recognized_artifact_id = None
        recognized_artifact_name = None
        db_context = ""

        # 1. Handle Audio (STT)
        if audio_bytes and len(audio_bytes) > 800:
            try:
                stt_text, det_lang = await asyncio.wait_for(
                    self._stt.transcribe(
                        audio_bytes, audio_filename, audio_content_type, lang_code
                    ),
                    timeout=STT_TIMEOUT
                )
                if stt_text.strip():
                    final_query = stt_text
                    detected_lang = det_lang
            except Exception as e:
                _LOGGER.error(f"STT failed or timed out: {e}")

        # 2. Handle Image (Vision)
        if image_base64:
            try:
                vision_result = await asyncio.wait_for(
                    recognize_image(image_base64, lang=lang_code),
                    timeout=VISION_TIMEOUT
                )
                if vision_result.recognized:
                    recognized_artifact_id = vision_result.artifact_id
                    # Fetch artifact details for context
                    db_context = await get_artifact_context_by_id(
                        recognized_artifact_id, context["db_field"]
                    )
                    recognized_artifact_name = vision_result.raw_label
                    
                    # If the user didn't ask anything specific, we set a default prompt
                    if not final_query:
                        final_query = f"[User sent an image of {recognized_artifact_name}]"
            except Exception as e:
                _LOGGER.error(f"Vision failed or timed out: {e}")

        # 3. If no image but query exists, try searching DB for artifact context (RAG)
        if not db_context and final_query:
            try:
                db_context = await get_artifact_context(final_query, context["db_field"])
            except Exception as e:
                _LOGGER.error(f"DB context lookup failed: {e}")

        # 4. Prepare LLM Context
        history_context = self._memory.format_history(session_id or "")
        system_prompt = build_voice_system_prompt(lang_code)
        
        # Build a rich prompt context
        llm_context_parts = [system_prompt]
        if history_context:
            llm_context_parts.append(f"CONVERSATION_HISTORY:\n{history_context}")
        
        if db_context and "No matching artifact" not in db_context:
            llm_context_parts.append(f"DB_CONTEXT:\n{db_context}")
        else:
            llm_context_parts.append("GENERAL_CHAT: Respond naturally as a guide.")

        llm_full_context = "\n\n".join(llm_context_parts)

        # 5. Generate LLM Response
        try:
            response_text = await asyncio.wait_for(
                self._llm.generate_response(
                    final_query, llm_full_context, lang_code
                ),
                timeout=LLM_TIMEOUT
            )
        except Exception as e:
            _LOGGER.error(f"LLM generation failed or timed out: {e}")
            response_text = "I'm sorry, I encountered an error while processing your request." if lang_code == "en" else "Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu của bạn."

        # 6. Save to Memory
        if session_id:
            if final_query:
                self._memory.add_turn(session_id, "user", final_query)
            self._memory.add_turn(session_id, "assistant", response_text)

        # 7. Generate Audio Response (TTS)
        synthesized_audio = None
        try:
            synthesized_audio = await asyncio.wait_for(
                self._tts.synthesize(response_text, lang_code),
                timeout=TTS_TIMEOUT
            )
        except Exception as e:
            _LOGGER.error(f"TTS failed or timed out: {e}")

        return UnifiedChatResult(
            response_text=response_text,
            audio_bytes=synthesized_audio,
            transcript=final_query,
            artifact_id=recognized_artifact_id,
            artifact_name=recognized_artifact_name,
            detected_lang=detected_lang
        )
