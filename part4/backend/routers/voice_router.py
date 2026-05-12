"""FastAPI router for voice chat requests."""

from __future__ import annotations

import base64
import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from services.voice.conversation_memory import ConversationMemory
from services.voice.edge_tts_provider import EdgeTTSProvider
from services.voice.gemini_llm import GeminiLLMProvider
from services.voice.groq_llm import GroqLLMProvider
from services.voice.groq_stt import GroqSTTProvider
from services.voice.language_manager import LanguageManager
from services.voice.llm_fallback import FallbackLLMProvider
from services.voice.sqlserver_db import get_artifact_context, get_artifact_context_by_id
from services.voice.voice_pipeline import VoiceOrchestrator


voice_router = APIRouter()
_LOGGER = logging.getLogger(__name__)
_MEMORY = ConversationMemory()

# Pre-initialize providers to reduce latency
_STT_PROVIDER = None
_LLM_PROVIDER = None
_TTS_PROVIDER = None


def _get_stt_provider():
    global _STT_PROVIDER
    if _STT_PROVIDER is None:
        _STT_PROVIDER = GroqSTTProvider()
    return _STT_PROVIDER


def _get_tts_provider():
    global _TTS_PROVIDER
    if _TTS_PROVIDER is None:
        _TTS_PROVIDER = EdgeTTSProvider()
    return _TTS_PROVIDER


def _llm_provider_order() -> list[str]:
    raw = os.getenv("LLM_PROVIDER_ORDER", "gemini,groq")
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _build_llm_provider():
    global _LLM_PROVIDER
    if _LLM_PROVIDER is not None:
        return _LLM_PROVIDER

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
        _LLM_PROVIDER = providers[0]
    else:
        _LLM_PROVIDER = FallbackLLMProvider(providers)
    
    return _LLM_PROVIDER


@voice_router.post("/api/voice/chat")
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
            audio.filename,
            audio.content_type,
            lang,
        )
        try:
            stt = _get_stt_provider()
            llm = _build_llm_provider()
            tts = _get_tts_provider()
        except Exception as err:
            _LOGGER.error("Failed to initialize providers: %s", err)
            raise HTTPException(status_code=500, detail=str(err)) from err

        orchestrator = VoiceOrchestrator(
            stt,
            llm,
            tts,
            db_lookup=get_artifact_context,
            memory=_MEMORY,
        )
        try:
            prefetched_context = None
            if artifact_id:
                try:
                    context = LanguageManager().setup_context(lang)
                    prefetched_context = get_artifact_context_by_id(
                        artifact_id,
                        context["db_field"],
                    )
                except Exception as exc:
                    _LOGGER.warning("Artifact prefetch failed: %s", exc)

            audio_bytes = await audio.read()
            result = await orchestrator.process_voice_request(
                audio_bytes,
                lang,
                audio.filename,
                audio.content_type,
                session_id,
                artifact_name,
                prefetched_context,
            )
            _LOGGER.info(
                "voice_chat request completed filename=%s response_bytes=%d",
                audio.filename,
                len(result.audio_bytes),
            )
            audio_b64 = base64.b64encode(result.audio_bytes).decode("ascii")
            return JSONResponse(
                content={
                    "audio_base64": audio_b64,
                    "audio_mime": "audio/mpeg",
                    "transcript": result.transcript,
                    "response_text": result.response_text,
                    "lang": result.lang,
                    "detected_lang": result.detected_lang,
                }
            )
        except ValueError as err:
            detail = str(err)
            status_code = 500

            if "Unsupported language" in detail:
                status_code = 400

            raise HTTPException(status_code=status_code, detail=detail) from err
    except HTTPException:
        raise
    except Exception as exc:
        _LOGGER.exception("Unhandled voice_chat error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc