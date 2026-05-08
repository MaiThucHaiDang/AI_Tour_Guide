"""FastAPI router for voice chat requests."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from services.voice.edge_tts_provider import EdgeTTSProvider
from services.voice.groq_llm import GroqLLMProvider
from services.voice.groq_stt import GroqSTTProvider
from services.voice.voice_pipeline import VoiceOrchestrator


voice_router = APIRouter()


@voice_router.post("/api/voice/chat")
async def voice_chat(audio: UploadFile = File(...), lang: str = Form(...)) -> Response:
    """Process a voice chat request and return synthesized audio."""
    try:
        try:
            stt = GroqSTTProvider()
            llm = GroqLLMProvider()
            tts = EdgeTTSProvider()
        except ValueError as err:
            # Missing API keys or other provider configuration problems
            raise HTTPException(status_code=500, detail=str(err)) from err

        orchestrator = VoiceOrchestrator(stt, llm, tts)
        try:
            audio_bytes = await audio.read()
            response_bytes = await orchestrator.process_voice_request(audio_bytes, lang)
            return Response(content=response_bytes, media_type="audio/mpeg")
        except ValueError as err:
            detail = str(err)
            status_code = 400 if "Unsupported language" in detail else 500
            raise HTTPException(status_code=status_code, detail=detail) from err
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc