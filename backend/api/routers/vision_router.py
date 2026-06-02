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

    # 1. Image recognition (Gemini Vision)
    logger.info(f"Recognize request received, lang={lang}, session_id={session_id}")
    vision_result = await recognize_image(
        body.image_base64, 
        lang=lang,
        lat=body.lat,
        lng=body.lng
    )

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
            },
        }

        final_error = "UNRECOGNIZED"
        if "429" in error_code:
            final_error = "429"
        elif "401" in error_code:
            final_error = "401"
        elif error_code in messages:
            final_error = error_code

        msg_map = messages.get(final_error, messages["UNRECOGNIZED"])

        return RecognizeResponse(
            success=False,
            error_code=error_code,
            confidence_score=vision_result.confidence_score,
            message=msg_map.get(lang, msg_map["vi"]),
        )

    artifact_id = vision_result.artifact_id

    # 2. Database lookup
    artifact_data = await get_artifact_by_id(artifact_id)

    if not artifact_data:
        logger.warning(f"artifact_id '{artifact_id}' not found in DB")
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
        logger.error("LLM error: %s", e)
        raise HTTPException(
            status_code=502, detail="LLM service tạm thời không khả dụng"
        )

    # 4. Return result
    artifact_name = artifact_data.name_vi if lang == "vi" else artifact_data.name_en
    logger.info(f"Success: {artifact_id}, lang={lang}")

    # 5. Save to memory if session_id exists to maintain context
    if session_id:
        memory.add_turn(session_id, "user", f"[User sent an image of {artifact_name}]")
        memory.add_turn(session_id, "assistant", llm_response.response_text)

    return RecognizeResponse(
        success=True,
        artifact_id=artifact_id,
        artifact_name=artifact_name,
        response_text=llm_response.response_text,
        confidence_score=vision_result.confidence_score,
    )
