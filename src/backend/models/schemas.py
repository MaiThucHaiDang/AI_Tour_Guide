"""
models/schemas.py
-----------------
Định nghĩa các Pydantic model dùng chung toàn bộ backend.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─── Request / Response cho Image Recognition ───────────────────────────────

class RecognizeRequest(BaseModel):
    """Payload nhận từ Mobile App (Người 1)."""
    image_base64: str = Field(..., description="Ảnh được encode sang base64")
    lang: str = Field(default="vi", description="Ngôn ngữ trả về: 'vi' hoặc 'en'")


class ArtifactInfo(BaseModel):
    """Thông tin hiện vật lấy từ DB (Người 5 cung cấp schema)."""
    art_id: str
    name_vi: str
    name_en: str
    history_text_vi: str
    history_text_en: str
    author: Optional[str] = None
    year: Optional[int] = None
    loc_id: str


class RecognizeResponse(BaseModel):
    """Response trả về cho Mobile App sau khi nhận diện + sinh câu trả lời."""
    success: bool
    artifact_id: Optional[str] = None
    artifact_name: Optional[str] = None      # Tên hiện vật theo ngôn ngữ
    response_text: Optional[str] = None      # Câu trả lời của LLM
    confidence_score: Optional[float] = None
    error_code: Optional[str] = None         # "LOW_CONFIDENCE" | "UNRECOGNIZED" | "DB_NOT_FOUND"
    message: Optional[str] = None            # Thông báo lỗi thân thiện


# ─── Internal service models ─────────────────────────────────────────────────

class VisionResult(BaseModel):
    """Kết quả trả về từ Image Recognition Service."""
    recognized: bool
    raw_label: Optional[str] = None          # Label thô từ Google Vision
    artifact_id: Optional[str] = None        # Sau khi map label → DB
    confidence_score: float = 0.0
    error: Optional[str] = None


class LLMRequest(BaseModel):
    """Input cho LLM Orchestrator."""
    artifact_id: str
    artifact_data: ArtifactInfo
    lang: str = "vi"


class LLMResponse(BaseModel):
    """Output từ LLM Orchestrator."""
    response_text: str
    token_count: int
    model_used: str