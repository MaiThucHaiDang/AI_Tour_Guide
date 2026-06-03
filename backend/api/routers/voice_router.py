"""Voice chat API router.

Moved from: part4/backend/routers/voice_router.py
All business logic preserved. Now uses dependency injection.
"""

from __future__ import annotations

import base64
import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.config import settings
from core.dependencies import (
    get_stt_provider,
    get_llm_provider,
    get_tts_provider,
    get_conversation_memory,
)
from core.security import limiter
from repositories.artifact_repository import get_artifact_context, get_artifact_context_by_id
from schemas.voice import VoiceChatResponse
from utils.language_manager import LanguageManager, get_language_manager
from orchestrators.voice_orchestrator import MIN_AUDIO_BYTES, VoiceOrchestrator
from utils.request_validation import normalize_lang, validate_audio_size

router = APIRouter(prefix="/api/v1", tags=["Voice"])
_LOGGER = logging.getLogger(__name__)


@router.post("/voice/chat")
@limiter.limit(settings.RATE_LIMIT)
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    lang: str = Form(...),
    session_id: str | None = Form(None),
    artifact_id: str | None = Form(None),
    artifact_name: str | None = Form(None),
) -> VoiceChatResponse:
    """Process a voice chat request and return synthesized audio."""
    try:
        lang = normalize_lang(lang)
        _LOGGER.info(
            "voice_chat request started filename=%s content_type=%s lang=%s",
            audio.filename, audio.content_type, lang,
        )
        audio_bytes = await audio.read()
        validate_audio_size(audio_bytes)

        try:
            tts = get_tts_provider()
            memory = get_conversation_memory()
            if len(audio_bytes) >= MIN_AUDIO_BYTES:
                stt = get_stt_provider()
                llm = get_llm_provider()
            else:
                stt = None
                llm = None
        except Exception as err:
            _LOGGER.error("Failed to initialize providers: %s", err)
            raise HTTPException(
                status_code=503,
                detail="Không khởi tạo được AI provider. Vui lòng kiểm tra .env.",
            ) from err

        orchestrator = VoiceOrchestrator(
            stt, llm, tts,
            db_lookup=get_artifact_context,
            memory=memory,
        )

        try:
            prefetched_context = None
            if artifact_id:
                try:
                    lang_manager = get_language_manager()
                    context = lang_manager.setup_context(lang)
                    prefetched_context = await get_artifact_context_by_id(
                        artifact_id, context["db_field"],
                    )
                except Exception as exc:
                    _LOGGER.warning("Artifact prefetch failed: %s", exc, exc_info=True)

            result = await orchestrator.process_voice_request(
                audio_bytes, lang, audio.filename, audio.content_type,
                session_id, artifact_name, prefetched_context,
            )

            _LOGGER.info(
                "voice_chat completed filename=%s response_bytes=%d",
                audio.filename, len(result.audio_bytes),
            )

            audio_b64 = base64.b64encode(result.audio_bytes).decode("ascii")
            return VoiceChatResponse(
                audio_base64=audio_b64,
                audio_mime="audio/mpeg",
                transcript=result.transcript,
                response_text=result.response_text,
                lang=result.lang,
                detected_lang=result.detected_lang,
            )

        except ValueError as err:
            detail = str(err)
            status_code = 400 if "Unsupported language" in detail else 500
            raise HTTPException(status_code=status_code, detail=detail) from err

    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Unhandled voice_chat error")
        raise HTTPException(
            status_code=500,
            detail="Không xử lý được giọng nói lúc này. Vui lòng thử lại.",
        ) from exc


@router.post("/voice/chat/stream")
@limiter.limit(settings.RATE_LIMIT)
async def voice_chat_stream(
    request: Request,
    audio: UploadFile = File(...),
    lang: str = Form(...),
    session_id: str | None = Form(None),
    artifact_id: str | None = Form(None),
    artifact_name: str | None = Form(None),
):
    """Process a voice chat request and return a stream of text chunks and final audio."""
    try:
        lang = normalize_lang(lang)
        audio_bytes = await audio.read()

        # Initialization logic (similar to non-stream version)
        try:
            tts = get_tts_provider()
            memory = get_conversation_memory()
            stt = get_stt_provider() if len(audio_bytes) >= MIN_AUDIO_BYTES else None
            llm = get_llm_provider() if len(audio_bytes) >= MIN_AUDIO_BYTES else None
        except Exception as err:
            _LOGGER.error("Failed to initialize providers: %s", err)
            raise HTTPException(status_code=503, detail="AI providers not ready")

        orchestrator = VoiceOrchestrator(
            stt, llm, tts, db_lookup=get_artifact_context, memory=memory
        )

        async def event_generator():
            try:
                prefetched_context = None
                if artifact_id:
                    try:
                        lang_manager = get_language_manager()
                        context_setup = lang_manager.setup_context(lang)
                        prefetched_context = await get_artifact_context_by_id(artifact_id, context_setup["db_field"])
                    except Exception as exc:
                        _LOGGER.warning("Artifact prefetch failed: %s", exc, exc_info=True)

                async for chunk in orchestrator.process_voice_request_stream(
                    audio_bytes, lang, audio.filename, audio.content_type,
                    session_id, artifact_name, prefetched_context
                ):
                    if chunk["type"] == "audio":
                        chunk["audio_base64"] = base64.b64encode(chunk["audio_bytes"]).decode("ascii")
                        chunk["audio_mime"] = "audio/mpeg"
                        del chunk["audio_bytes"]

                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                _LOGGER.error("Streaming error: %s", e)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as exc:
        _LOGGER.exception("Unhandled voice_chat_stream error")
        raise HTTPException(status_code=500, detail=str(exc))

