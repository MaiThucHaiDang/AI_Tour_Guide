"""
 Chụp ảnh → AI nhận diện → Trả lời giọng nói

Endpoints:
  POST /api/v1/recognize   - Nhận ảnh base64, trả về tên hiện vật + câu trả lời LLM
  GET  /api/v1/health      - Health check
  GET  /api/v1/artifacts   - Danh sách hiện vật (debug, tắt trên production)
"""
from dotenv import load_dotenv
load_dotenv()
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
from services.database import get_artifact_by_id, MOCK_ARTIFACTS

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
    logger.info(f"Số hiện vật trong mock DB: {len(MOCK_ARTIFACTS)}")
    yield
    logger.info("Backend tắt.")


app = FastAPI(
    title="AI Tour Guide - Backend API",
    description="Backend Tính năng 1: Chụp ảnh → Nhận diện hiện vật → Câu trả lời AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Đăng ký rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - cho phép Mobile App (Người 1) gọi từ thiết bị
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Production: thay bằng domain cụ thể
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/v1/health")
async def health_check():
    """Kiểm tra backend còn sống không. Mobile App ping định kỳ."""
    return {"status": "ok", "service": "AI Tour Guide Backend v1"}


# ─── Endpoint chính: Nhận diện ảnh ───────────────────────────────────────────
@app.post("/api/v1/recognize", response_model=RecognizeResponse)
@limiter.limit("30/minute")   # Mỗi IP tối đa 30 request/phút
async def recognize_artifact(request: Request, body: RecognizeRequest):
    """
    Endpoint chính - Luồng đầy đủ:
    
      1. Nhận ảnh base64 từ Mobile App (Người 1)
      2. Gọi Image Recognition Service → artifact_id
      3. Query DB → lấy thông tin hiện vật
      4. Gọi LLM Orchestrator → sinh câu trả lời
      5. Trả về tên hiện vật + câu trả lời cho Mobile App
      
      (TTS: Mobile App nhận response_text rồi gọi riêng TTS Service của Người 4)
    
    Error codes:
      - LOW_CONFIDENCE: Ảnh tối/mờ, confidence < 0.5
      - UNRECOGNIZED: Không nhận diện được hiện vật
      - DB_NOT_FOUND: artifact_id không có trong DB
    """
    lang = body.lang if body.lang in ("vi", "en") else "vi"

    # ── Bước 1: Nhận diện ảnh ─────────────────────────────────────────────────
    logger.info(f"Nhận request nhận diện ảnh, lang={lang}")
    vision_result = await recognize_image(body.image_base64)

    if not vision_result.recognized:
        error_code = vision_result.error or "UNRECOGNIZED"

        # Chọn thông báo lỗi thân thiện theo ngôn ngữ
        messages = {
            "LOW_CONFIDENCE": {
                "vi": "Ảnh chưa rõ nét. Vui lòng chụp lại ở góc chính diện, đủ sáng.",
                "en": "Image is unclear. Please retake with better lighting and a straight angle.",
            },
            "UNRECOGNIZED": {
                "vi": "Không nhận diện được hiện vật. Hãy thử chụp toàn bộ công trình.",
                "en": "Could not identify the artifact. Try capturing the full structure.",
            },
        }
        msg_map = messages.get(error_code, messages["UNRECOGNIZED"])
        
        return RecognizeResponse(
            success=False,
            error_code=error_code,
            confidence_score=vision_result.confidence_score,
            message=msg_map.get(lang, msg_map["vi"]),
        )

    artifact_id = vision_result.artifact_id

    # ── Bước 2: Lấy thông tin từ DB ───────────────────────────────────────────
    artifact_data = await get_artifact_by_id(artifact_id)

    if not artifact_data:
        logger.warning(f"artifact_id '{artifact_id}' không tìm thấy trong DB")
        return RecognizeResponse(
            success=False,
            artifact_id=artifact_id,
            error_code="DB_NOT_FOUND",
            message=(
                "Hiện chưa có dữ liệu cho hiện vật này."
                if lang == "vi"
                else "No data available for this artifact yet."
            ),
        )

    # ── Bước 3: Gọi LLM Orchestrator ──────────────────────────────────────────
    try:
        llm_response = await generate_response(artifact_data=artifact_data, lang=lang)
    except Exception as e:
        logger.error(f"LLM lỗi: {e}")
        raise HTTPException(status_code=502, detail="LLM service tạm thời không khả dụng")

    # ── Bước 4: Trả kết quả về Mobile App ─────────────────────────────────────
    artifact_name = (
        artifact_data.name_vi if lang == "vi" else artifact_data.name_en
    )

    logger.info(f"Thành công: {artifact_id}, lang={lang}")

    return RecognizeResponse(
        success=True,
        artifact_id=artifact_id,
        artifact_name=artifact_name,
        response_text=llm_response.response_text,
        confidence_score=vision_result.confidence_score,
    )


# ─── Debug endpoint: Danh sách hiện vật ──────────────────────────────────────
@app.get("/api/v1/artifacts")
async def list_artifacts():
    """
    Trả về danh sách hiện vật trong DB (chỉ dùng để debug / dev).
    TODO: Tắt endpoint này trên production.
    """
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "total": len(MOCK_ARTIFACTS),
        "artifacts": [
            {"art_id": k, "name_vi": v["name_vi"], "name_en": v["name_en"]}
            for k, v in MOCK_ARTIFACTS.items()
        ],
    }


# ─── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Lỗi không xử lý được: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Lỗi server nội bộ. Vui lòng thử lại."},
    )


# ─── Chạy trực tiếp ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)