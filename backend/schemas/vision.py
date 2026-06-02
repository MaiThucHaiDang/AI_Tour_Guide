"""Pydantic schemas for the vision (image recognition) pipeline."""

from pydantic import BaseModel, Field
from typing import Optional


class RecognizeRequest(BaseModel):
    """Payload from the frontend for image recognition."""
    image_base64: str = Field(..., description="Base64 encoded image")
    lang: str = Field(default="vi", description="Response language: 'vi' or 'en'")
    session_id: Optional[str] = Field(default=None, description="Optional session ID for chat memory")
    lat: Optional[float] = Field(default=None, description="Latitude")
    lng: Optional[float] = Field(default=None, description="Longitude")


class ArtifactInfo(BaseModel):
    """Artifact data retrieved from the database."""
    art_id: str
    name_vi: str
    name_en: str
    history_text_vi: str
    history_text_en: str
    author: Optional[str] = None
    year: Optional[int] = None
    loc_id: str


class VisionResult(BaseModel):
    """Result from the image recognition service."""
    recognized: bool
    raw_label: Optional[str] = None
    artifact_id: Optional[str] = None
    confidence_score: float = 0.0
    error: Optional[str] = None


class LLMResponse(BaseModel):
    """Output from the LLM orchestrator."""
    response_text: str
    token_count: int
    model_used: str


class RecognizeResponse(BaseModel):
    """Response returned to the frontend after recognition + LLM."""
    success: bool
    artifact_id: Optional[str] = None
    artifact_name: Optional[str] = None
    response_text: Optional[str] = None
    confidence_score: Optional[float] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
