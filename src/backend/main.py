"""
Chụp ảnh → AI nhận diện → Trả lời giọng nói

Endpoints:
  POST /api/v1/recognize   - Nhận ảnh base64, trả về tên hiện vật + câu trả lời LLM
  GET  /api/v1/health      - Health check
"""
from pathlib import Path
from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_ROOT.parents[1]
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv(_REPO_ROOT / ".env", override=False)

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from models.schemas import RecognizeRequest, RecognizeResponse
from services.image_recognition import recognize_image
from services.llm_orchestrator import generate_response
from services.database import get_artifact_by_id  # Đã loại bỏ MOCK_ARTIFACTS

# ─── Cấu hình logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Tour Guide Backend khởi động...")
    logger.info(f"Môi trường: {os.getenv('ENVIRONMENT', 'development')}")
    # Đã xóa dòng log tham chiếu đến MOCK_ARTIFACTS
    yield
    logger.info("Backend tắt.")


app = FastAPI(
    title="AI Tour Guide - Backend API",
    description="Backend Tính năng 1: Chụp ảnh → Nhận diện hiện vật → Câu trả lời AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Đảm bảo origins không có dấu / ở cuối để tránh lỗi trình duyệt
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:5173", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "AI Tour Guide Backend v1"}


# ─── Endpoint chính: Nhận diện ảnh ───────────────────────────────────────────
@app.post("/api/v1/recognize", response_model=RecognizeResponse)
@limiter.limit("30/minute")
async def recognize_artifact(request: Request, body: RecognizeRequest):
    lang = body.lang if body.lang in ("vi", "en") else "vi"

    # 1. Nhận diện ảnh (Sử dụng Gemini Vision)
    logger.info(f"Nhận request nhận diện ảnh, lang={lang}")
    vision_result = await recognize_image(body.image_base64)

    if not vision_result.recognized:
        error_code = vision_result.error or "UNRECOGNIZED"
        messages = {
            "LOW_CONFIDENCE": {
                "vi": "Ảnh chưa rõ nét. Vui lòng chụp lại ở góc chính diện, đủ sáng.",
                "en": "Image is unclear. Please retake with better lighting and a straight angle.",
            },
            "UNRECOGNIZED": {
                "vi": "Không nhận diện được hiện vật. Hãy thử chụp toàn bộ công trình.",
                "en": "Could not identify the artifact. Try capturing the full structure.",
            },
            "429": {
                "vi": "AI đang bận (Hết lượt dùng thử). Vui lòng thử lại sau 1 phút.",
                "en": "AI is busy (Quota exceeded). Please retry in 1 minute.",
            },
            "401": {
                "vi": "Lỗi xác thực (API Key không hợp lệ). Vui lòng kiểm tra file .env.",
                "en": "Authentication error (Invalid API Key). Please check your .env file.",
            }
        }

        final_error = "UNRECOGNIZED"
        if "429" in error_code: final_error = "429"
        elif "401" in error_code: final_error = "401"
        elif error_code in messages: final_error = error_code

        msg_map = messages.get(final_error, messages["UNRECOGNIZED"])
        
        return RecognizeResponse(
            success=False,
            error_code=error_code,
            confidence_score=vision_result.confidence_score,
            message=msg_map.get(lang, msg_map["vi"]),
        )

    artifact_id = vision_result.artifact_id

    # 2. Lấy thông tin từ SQL Server (Thông qua service đã cập nhật)
    artifact_data = await get_artifact_by_id(artifact_id)

    if not artifact_data:
        logger.warning(f"artifact_id '{artifact_id}' không tìm thấy trong DB")
        return RecognizeResponse(
            success=False,
            artifact_id=artifact_id,
            error_code="DB_NOT_FOUND",
            message=("Hiện chưa có dữ liệu cho hiện vật này." if lang == "vi" else "No data available."),
        )

    # 3. Gọi LLM sinh câu trả lời
    try:
        llm_response = await generate_response(artifact_data=artifact_data, lang=lang)
    except Exception as e:
        logger.error(f"LLM lỗi: {e}")
        raise HTTPException(status_code=502, detail="LLM service tạm thời không khả dụng")

    # 4. Trả kết quả
    artifact_name = artifact_data.name_vi if lang == "vi" else artifact_data.name_en
    logger.info(f"Thành công: {artifact_id}, lang={lang}")

    return RecognizeResponse(
        success=True,
        artifact_id=artifact_id,
        artifact_name=artifact_name,
        response_text=llm_response.response_text,
        confidence_score=vision_result.confidence_score,
    )


# ─── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Lỗi không xử lý được: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Lỗi server nội bộ. Vui lòng thử lại."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)