"""Unified chat API router.

Handles Text, Voice, and Vision inputs in a single endpoint.
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from core.config import settings
from core.dependencies import (
    get_stt_provider,
    get_llm_provider,
    get_tts_provider,
    get_conversation_memory,
)
from core.security import limiter
from orchestrators.unified_orchestrator import MIN_AUDIO_BYTES, UnifiedOrchestrator
from schemas.voice import UnifiedChatResponse
from utils.request_validation import (
    normalize_lang,
    validate_audio_size,
    validate_image_base64_size,
    validate_text_size,
)

router = APIRouter(prefix="/api/v1", tags=["Chat"])
_LOGGER = logging.getLogger(__name__)

@router.post("/chat/unified")
@limiter.limit(settings.RATE_LIMIT)
async def unified_chat(
    request: Request,
    text: Optional[str] = Form(None),
    image_base64: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    lang: str = Form("vi"),
    session_id: Optional[str] = Form(None),
) -> UnifiedChatResponse:
    """Process a multimodal chat request."""
    try:
        lang = normalize_lang(lang)
        validate_text_size(text)
        validate_image_base64_size(image_base64)

        _LOGGER.info("Unified chat request: lang=%s, session_id=%s, has_text=%s, has_image=%s, has_audio=%s", 
                     lang, session_id, text is not None, image_base64 is not None, audio is not None)
        
        stt = None
        tts = None
        audio_bytes = None
        audio_filename = None
        audio_content_type = None
        
        if audio:
            audio_bytes = await audio.read()
            validate_audio_size(audio_bytes)
            audio_filename = audio.filename
            audio_content_type = audio.content_type
            if len(audio_bytes) >= MIN_AUDIO_BYTES:
                try:
                    stt = get_stt_provider()
                    tts = get_tts_provider()
                except Exception as err:
                    _LOGGER.warning("Voice provider initialization failed: %s", err)
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Chưa cấu hình voice provider. Hãy kiểm tra GROQ_API_KEY "
                            "trong file .env rồi khởi động lại backend."
                        ),
                    ) from err

        memory = get_conversation_memory()
        
        orchestrator = UnifiedOrchestrator(
            stt,
            None,
            tts,
            memory,
            llm_factory=get_llm_provider,
            tts_factory=get_tts_provider,
        )
            
        result = await orchestrator.process_chat_request(
            text_query=text,
            audio_bytes=audio_bytes,
            image_base64=image_base64,
            lang=lang,
            session_id=session_id,
            audio_filename=audio_filename,
            audio_content_type=audio_content_type
        )
        
        audio_b64 = None
        if result.audio_bytes:
            audio_b64 = base64.b64encode(result.audio_bytes).decode("ascii")
            
        return UnifiedChatResponse(
            success=True,
            response_text=result.response_text,
            audio_base64=audio_b64,
            audio_mime="audio/mpeg",
            transcript=result.transcript,
            artifact_id=result.artifact_id,
            artifact_name=result.artifact_name,
            detected_lang=result.detected_lang,
            answer_source=result.answer_source,
            processing_steps=result.processing_steps,
            artifact_year=result.artifact_year,
            artifact_author=result.artifact_author,
            artifact_summary=result.artifact_summary,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Unified chat error")
        raise HTTPException(
            status_code=500,
            detail="Không xử lý được yêu cầu lúc này. Vui lòng thử lại.",
        ) from exc
