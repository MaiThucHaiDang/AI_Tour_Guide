"""FastAPI router for voice chat requests."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from services.voice.edge_tts_provider import EdgeTTSProvider
from services.voice.gemini_llm import GeminiLLMProvider
from services.voice.groq_llm import GroqLLMProvider
from services.voice.groq_stt import GroqSTTProvider
from services.voice.llm_fallback import FallbackLLMProvider
from services.voice.sqlserver_db import get_artifact_context
from services.voice.voice_pipeline import VoiceOrchestrator


voice_router = APIRouter()
_LOGGER = logging.getLogger(__name__)


def _llm_provider_order() -> list[str]:
    raw = os.getenv("LLM_PROVIDER_ORDER", "gemini,groq")
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _build_llm_provider():
    errors: list[str] = []
    providers = []
    for provider in _llm_provider_order():
        try:
            if provider == "groq":
                providers.append(GroqLLMProvider())
                continue
            if provider == "gemini":
                providers.append(GeminiLLMProvider())
                continue
            errors.append(f"Unknown provider '{provider}'")
        except Exception as exc:
            _LOGGER.warning("LLM provider %s init failed: %s", provider, exc)
            errors.append(f"{provider}: {exc}")

    if not providers:
        raise ValueError("No LLM provider available. " + "; ".join(errors))
    if len(providers) == 1:
        return providers[0]
    return FallbackLLMProvider(providers)


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
            llm = _build_llm_provider()
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
            status_code = 500

            if "Unsupported language" in detail:
                status_code = 400
            elif "Audio payload too small" in detail:
                status_code = 400
                detail = "audio qua ngan"
            elif "Empty transcription" in detail:
                status_code = 400
                detail = "transcription rong"
            elif "Empty audio payload" in detail:
                status_code = 400
                detail = "audio rong"

            raise HTTPException(status_code=status_code, detail=detail) from err
    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Unhandled voice_chat error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc