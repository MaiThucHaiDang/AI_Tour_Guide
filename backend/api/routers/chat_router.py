"""Unified chat API router.

Handles Text, Voice, and Vision inputs in a single endpoint.
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import JSONResponse

from core.dependencies import (
    get_stt_provider,
    get_llm_provider,
    get_tts_provider,
    get_conversation_memory,
)
from orchestrators.unified_orchestrator import UnifiedOrchestrator

router = APIRouter(prefix="/api/v1", tags=["Chat"])
_LOGGER = logging.getLogger(__name__)

@router.post("/chat/unified")
async def unified_chat(
    text: Optional[str] = Form(None),
    image_base64: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    lang: str = Form("vi"),
    session_id: Optional[str] = Form(None),
) -> JSONResponse:
    """Process a multimodal chat request."""
    try:
        _LOGGER.info("Unified chat request: lang=%s, session_id=%s, has_text=%s, has_image=%s, has_audio=%s", 
                     lang, session_id, text is not None, image_base64 is not None, audio is not None)
        
        stt = get_stt_provider()
        llm = get_llm_provider()
        tts = get_tts_provider()
        memory = get_conversation_memory()
        
        orchestrator = UnifiedOrchestrator(stt, llm, tts, memory)
        
        audio_bytes = None
        audio_filename = None
        audio_content_type = None
        
        if audio:
            audio_bytes = await audio.read()
            audio_filename = audio.filename
            audio_content_type = audio.content_type
            
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
            
        return JSONResponse(content={
            "success": True,
            "response_text": result.response_text,
            "audio_base64": audio_b64,
            "audio_mime": "audio/mpeg",
            "transcript": result.transcript,
            "artifact_id": result.artifact_id,
            "artifact_name": result.artifact_name,
            "detected_lang": result.detected_lang,
        })
        
    except Exception as exc:
        _LOGGER.exception("Unified chat error")
        raise HTTPException(status_code=500, detail=str(exc))
