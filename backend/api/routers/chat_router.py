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
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    artifact_id: Optional[int] = Form(None),
) -> UnifiedChatResponse:
    """Process a multimodal chat request."""
    try:
        # Validate inputs
        lang = normalize_lang(lang)
        validate_text_size(text)
        validate_image_base64_size(image_base64)
        
        # Validate session_id if provided
        if session_id and len(session_id) > 255:
            raise HTTPException(
                status_code=400,
                detail="session_id quá dài (max 255 ký tự)"
            )
        
        # Validate GPS coordinates
        if lat is not None and not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400,
                detail="Latitude phải nằm trong khoảng [-90, 90]"
            )
        if lng is not None and not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=400,
                detail="Longitude phải nằm trong khoảng [-180, 180]"
            )
        
        # Ensure artifact_id is positive if provided
        if artifact_id is not None and artifact_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="artifact_id phải là số dương"
            )

        _LOGGER.info(
            "Unified chat request: lang=%s, session_id=%s, has_text=%s, has_image=%s, has_audio=%s, artifact_id=%s", 
            lang, session_id, text is not None, image_base64 is not None, audio is not None, artifact_id
        )
        
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
            audio_content_type=audio_content_type,
            artifact_id=artifact_id
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
            artifact_id=str(result.artifact_id) if result.artifact_id is not None else None,
            artifact_name=result.artifact_name,
            detected_lang=result.detected_lang,
            answer_source=result.answer_source,
            processing_steps=result.processing_steps,
            artifact_year=result.artifact_year,
            artifact_author=result.artifact_author,
            artifact_summary=result.artifact_summary,
            tts_token=result.tts_token,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Unified chat error")
        raise HTTPException(
            status_code=500,
            detail="Không xử lý được yêu cầu lúc này. Vui lòng thử lại.",
        ) from exc


@router.get("/tts/fetch")
async def fetch_tts_audio(
    tts_token: str,
):
    """Poll for background TTS audio result by token.

    Returns:
      - status "ready" with audio_base64 when synthesis is complete.
      - status "pending" when synthesis is still in progress.
    """
    if not tts_token or len(tts_token) > 64:
        raise HTTPException(status_code=400, detail="Invalid tts_token")

    audio_bytes = UnifiedOrchestrator.fetch_tts_audio(tts_token)
    if audio_bytes:
        return {
            "status": "ready",
            "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
            "audio_mime": "audio/mpeg",
        }
    return {"status": "pending"}
