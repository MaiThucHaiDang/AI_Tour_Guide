"""Vision (image recognition) API router.

Extracted from: src/backend/main.py
All business logic preserved exactly.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, HTTPException, Depends

from core.config import settings
from core.security import limiter
from schemas.vision import RecognizeRequest, RecognizeResponse
from services.vision.image_recognition import recognize_image
from services.vision.response_generator import generate_response
from repositories.artifact_repository import get_artifact_by_id
from core.dependencies import get_conversation_memory
from services.memory.conversation_memory import ConversationMemory
from utils.request_validation import normalize_lang, validate_image_base64_size

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Vision"])


@router.post("/recognize", response_model=RecognizeResponse)
@limiter.limit(settings.RATE_LIMIT)
async def recognize_artifact(
    request: Request, 
    body: RecognizeRequest,
    memory: ConversationMemory = Depends(get_conversation_memory)
):
    lang = normalize_lang(body.lang)
    validate_image_base64_size(body.image_base64)
    session_id = body.session_id
    
    # Validate GPS coordinates if provided
    if body.lat is not None and not (-90 <= body.lat <= 90):
        raise HTTPException(
            status_code=400,
            detail="Latitude phải nằm trong khoảng [-90, 90]"
        )
    if body.lng is not None and not (-180 <= body.lng <= 180):
        raise HTTPException(
            status_code=400,
            detail="Longitude phải nằm trong khoảng [-180, 180]"
        )

    # 1. Image recognition (Gemini Vision)
    logger.info("Recognize request: lang=%s, session_id=%s, gps=(%s, %s)", 
                lang, session_id, body.lat, body.lng)
    
    vision_result = await recognize_image(
        body.image_base64, 
        lang=lang,
        lat=body.lat,
        lng=body.lng
    )
    
    logger.debug("Vision result: recognized=%s, error=%s, confidence=%.2f", 
                vision_result.recognized, vision_result.error, vision_result.confidence_score)

    if not vision_result.recognized:
        error_code = vision_result.error or "UNRECOGNIZED"
        messages = {
            "LOW_CONFIDENCE": {
                "vi": "Ảnh chưa rõ nét hoặc góc chụp không tốt. Vui lòng chụp lại ở góc chính diện, đủ sáng.",
                "en": "Image is unclear or angle is poor. Please retake with better lighting and a straight angle.",
            },
            "NOT_AN_ARTIFACT": {
                "vi": "Đây không phải là di tích hoặc công trình lịch sử. Hãy chụp một công trình trong Hoàng thành Huế.",
                "en": "This is not a historical artifact. Please capture a structure in the Hue Imperial Citadel.",
            },
            "UNRECOGNIZED": {
                "vi": "Không nhận diện được công trình này. Hãy thử chụp toàn bộ, ở góc khác hoặc với ánh sáng tốt hơn.",
                "en": "Could not identify this structure. Try capturing the full view or from a different angle with better lighting.",
            },
            "INVALID_IMAGE": {
                "vi": "Ảnh không hợp lệ hoặc bị lỗi. Vui lòng chọn ảnh JPG, PNG hoặc định dạng khác.",
                "en": "Invalid image format. Please select a JPG, PNG or other valid format.",
            },
            "VISION_EMPTY_RESPONSE": {
                "vi": "AI không thể xử lý ảnh này (bị lọc bởi cơ chế an toàn). Vui lòng thử ảnh khác.",
                "en": "AI could not process this image (safety filter). Please try another image.",
            },
            "API_ERROR": {
                "vi": "Lỗi kỹ thuật từ AI. Vui lòng thử lại sau ít phút.",
                "en": "Technical error from AI. Please retry in a moment.",
            },
            "429": {
                "vi": "AI đang bận (Hết lượt dùng thử). Vui lòng thử lại sau 1 phút.",
                "en": "AI is busy (Rate limit exceeded). Please retry in 1 minute.",
            },
            "401": {
                "vi": "Lỗi xác thực API. Vui lòng kiểm tra cấu hình .env.",
                "en": "API authentication error. Please check .env configuration.",
            },
        }

        final_error = error_code if error_code in messages else "UNRECOGNIZED"
        msg_map = messages.get(final_error, messages["UNRECOGNIZED"])

        logger.info("Vision recognition failed: error=%s, confidence=%.2f", final_error, vision_result.confidence_score)

        return RecognizeResponse(
            success=False,
            error_code=final_error,
            confidence_score=vision_result.confidence_score,
            message=msg_map.get(lang, msg_map["vi"]),
        )

    artifact_id = vision_result.artifact_id

    # 2. Database lookup
    artifact_data = await get_artifact_by_id(artifact_id)

    if not artifact_data:
        logger.warning("artifact_id '%s' not found in DB", artifact_id)
        return RecognizeResponse(
            success=False,
            artifact_id=artifact_id,
            error_code="DB_NOT_FOUND",
            message=(
                "Hiện chưa có dữ liệu cho hiện vật này."
                if lang == "vi"
                else "No data available."
            ),
        )

    # 3. LLM response generation
    try:
        llm_response = await generate_response(artifact_data=artifact_data, lang=lang)
    except Exception as e:
        logger.error("LLM error: %s", e, exc_info=True)
        artifact_name = artifact_data.name_vi if lang == "vi" else artifact_data.name_en
        fallback_text = (
            f"Đã nhận diện ảnh là {artifact_name}, nhưng phần tạo thuyết minh AI đang tạm thời quá tải. "
            "Bạn có thể mở địa điểm này để xem thông tin chi tiết hoặc thử hỏi lại sau ít phút."
            if lang == "vi"
            else f"The image was recognized as {artifact_name}, but the AI narration service is temporarily overloaded. "
            "You can open this stop for details or try again in a few minutes."
        )
        if session_id:
            await memory.add_turn(session_id, "user", f"[User sent an image of {artifact_name}]")
            await memory.add_turn(session_id, "assistant", fallback_text)
        return RecognizeResponse(
            success=True,
            artifact_id=artifact_id,
            artifact_name=artifact_name,
            response_text=fallback_text,
            confidence_score=vision_result.confidence_score,
            error_code="LLM_UNAVAILABLE",
            message=(
                "Đã nhận diện ảnh, nhưng AI thuyết minh đang quá tải."
                if lang == "vi"
                else "Image recognized, but AI narration is overloaded."
            ),
        )

    # 4. Return result
    artifact_name = artifact_data.name_vi if lang == "vi" else artifact_data.name_en
    logger.info("Success: %s, lang=%s", artifact_id, lang)

    # 5. Save to memory if session_id exists to maintain context
    if session_id:
        await memory.add_turn(session_id, "user", f"[User sent an image of {artifact_name}]")
        await memory.add_turn(session_id, "assistant", llm_response.response_text)

    return RecognizeResponse(
        success=True,
        artifact_id=artifact_id,
        artifact_name=artifact_name,
        response_text=llm_response.response_text,
        confidence_score=vision_result.confidence_score,
    )
