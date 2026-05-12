"""FastAPI router for voice chat requests."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from services.voice.edge_tts_provider import EdgeTTSProvider
from services.voice.groq_llm import GroqLLMProvider
from services.voice.groq_stt import GroqSTTProvider
from services.voice.sqlserver_db import get_artifact_context
from services.voice.voice_pipeline import VoiceOrchestrator


voice_router = APIRouter()
_LOGGER = logging.getLogger(__name__)


@voice_router.post("/api/voice/chat")
async def voice_chat(audio: UploadFile = File(...), lang: str = Form(...)) -> Response:
    """Process a voice chat request and return synthesized audio."""
    try:
        _LOGGER.info(
            "voice_chat request started filename=%s content_type=%s lang=%s",
            audio.filename,
            audio.content_type,
            lang,
        )
        try:
            stt = GroqSTTProvider()
            llm = GroqLLMProvider()
            tts = EdgeTTSProvider()
        except ValueError as err:
            # Missing API keys or other provider configuration problems
            raise HTTPException(status_code=500, detail=str(err)) from err

        orchestrator = VoiceOrchestrator(
            stt,
            llm,
            tts,
            db_lookup=get_artifact_context,
        )
        try:
            audio_bytes = await audio.read()
            response_bytes = await orchestrator.process_voice_request(
                audio_bytes,
                lang,
                audio.filename,
                audio.content_type,
            )
            _LOGGER.info(
                "voice_chat request completed filename=%s response_bytes=%d",
                audio.filename,
                len(response_bytes),
            )
            return Response(content=response_bytes, media_type="audio/mpeg")
        except ValueError as err:
            detail = str(err)
            status_code = 400 if "Unsupported language" in detail else 500
            raise HTTPException(status_code=status_code, detail=detail) from err
    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Unhandled voice_chat error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc