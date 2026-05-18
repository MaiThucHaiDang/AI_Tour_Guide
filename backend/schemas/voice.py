"""Pydantic schemas for the voice pipeline."""

from pydantic import BaseModel
from typing import Optional


class VoiceChatResponse(BaseModel):
    """Typed response for the voice chat endpoint."""
    audio_base64: str
    audio_mime: str = "audio/mpeg"
    transcript: str
    response_text: str
    lang: str
    detected_lang: str
