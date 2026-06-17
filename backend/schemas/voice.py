"""Pydantic schemas for the voice pipeline."""

from pydantic import BaseModel, Field
from typing import Optional


class VoiceChatResponse(BaseModel):
    """Typed response for the voice chat endpoint."""
    audio_base64: str
    audio_mime: str = "audio/mpeg"
    transcript: str
    response_text: str
    lang: str
    detected_lang: Optional[str] = None


class UnifiedChatResponse(BaseModel):
    """Typed response for the multimodal unified chat endpoint."""
    success: bool = True
    response_text: str
    speech_text: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_mime: str = "audio/mpeg"
    transcript: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_name: Optional[str] = None
    detected_lang: Optional[str] = None
    answer_source: str
    processing_steps: list[str] = Field(default_factory=list)
    artifact_year: Optional[int] = None
    artifact_author: Optional[str] = None
    artifact_summary: Optional[str] = None
    tts_token: Optional[str] = None
