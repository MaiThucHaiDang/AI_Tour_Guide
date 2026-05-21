"""Voice chat API router.

Moved from: part4/backend/routers/voice_router.py
All business logic preserved. Now uses dependency injection.
"""

from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from core.dependencies import (
    get_stt_provider,
    get_llm_provider,
    get_tts_provider,
    get_conversation_memory,
)
from repositories.artifact_repository import get_artifact_context, get_artifact_context_by_id
from utils.language_manager import LanguageManager
from orchestrators.voice_orchestrator import VoiceOrchestrator

router = APIRouter(prefix="/api/v1", tags=["Voice"])
_LOGGER = logging.getLogger(__name__)


@router.post("/voice/chat")
async def voice_chat(
    audio: UploadFile = File(...),
    lang: str = Form(...),
    session_id: str | None = Form(None),
    artifact_id: str | None = Form(None),
    artifact_name: str | None = Form(None),
) -> JSONResponse:
    """Process a voice chat request and return synthesized audio."""
    try:
        _LOGGER.info(
            "voice_chat request started filename=%s content_type=%s lang=%s",
            audio.filename, audio.content_type, lang,
        )
        try:
            stt = get_stt_provider()
            llm = get_llm_provider()
            tts = get_tts_provider()
            memory = get_conversation_memory()
        except Exception as err:
            _LOGGER.error("Failed to initialize providers: %s", err)
            raise HTTPException(status_code=500, detail=str(err)) from err

        orchestrator = VoiceOrchestrator(
            stt, llm, tts,
            db_lookup=get_artifact_context,
            memory=memory,
        )

        try:
            prefetched_context = None
            if artifact_id:
                try:
                    context = LanguageManager().setup_context(lang)
                    prefetched_context = await get_artifact_context_by_id(
                        artifact_id, context["db_field"],
                    )
                except Exception as exc:
                    _LOGGER.warning("Artifact prefetch failed: %s", exc)

            audio_bytes = await audio.read()
            result = await orchestrator.process_voice_request(
                audio_bytes, lang, audio.filename, audio.content_type,
                session_id, artifact_name, prefetched_context,
            )

            _LOGGER.info(
                "voice_chat completed filename=%s response_bytes=%d",
                audio.filename, len(result.audio_bytes),
            )

            audio_b64 = base64.b64encode(result.audio_bytes).decode("ascii")
            return JSONResponse(content={
                "audio_base64": audio_b64,
                "audio_mime": "audio/mpeg",
                "transcript": result.transcript,
                "response_text": result.response_text,
                "lang": result.lang,
                "detected_lang": result.detected_lang,
            })

        except ValueError as err:
            detail = str(err)
            status_code = 400 if "Unsupported language" in detail else 500
            raise HTTPException(status_code=status_code, detail=detail) from err

    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Unhandled voice_chat error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
