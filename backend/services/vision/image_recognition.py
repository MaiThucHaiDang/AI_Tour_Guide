"""Image recognition service using Gemini Vision.

Moved from: src/backend/services/image_recognition.py
Logic preserved exactly.
"""

from __future__ import annotations

import base64
import io
import json
import logging

from PIL import Image
import google.generativeai as genai

from core.config import settings
from schemas.vision import VisionResult
from services.artifacts.label_mapping import map_vision_label_to_artifact_id

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
_vision_model = genai.GenerativeModel(
    "gemini-flash-latest",
    generation_config={"response_mime_type": "application/json"}
)


async def recognize_image(image_base64: str) -> VisionResult:
    """Recognize an artifact from a base64-encoded image."""
    try:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        from utils.prompt_templates import VISION_RECOGNITION_PROMPT

        response = await _vision_model.generate_content_async(
            [VISION_RECOGNITION_PROMPT, image]
        )
        
        response_text = response.text.strip()
        logger.info(f"Gemini Vision raw response: {response_text}")

        if "KHÔNG BIẾT" in response_text.upper() or not response_text:
            return VisionResult(recognized=False, error="UNRECOGNIZED")

        try:
            data = json.loads(response_text)
            label = data.get("artifact_name", "")
            confidence = data.get("confidence", 0.9)
            is_artifact = data.get("is_historical_artifact", True)

            if not is_artifact or not label:
                return VisionResult(recognized=False, error="NOT_AN_ARTIFACT")

        except json.JSONDecodeError:
            # Fallback if AI didn't return valid JSON despite config
            label = response_text
            confidence = 0.8

        artifact_id = map_vision_label_to_artifact_id(label)

        if artifact_id:
            return VisionResult(
                recognized=True,
                raw_label=label,
                artifact_id=artifact_id,
                confidence_score=confidence,
            )

        return VisionResult(recognized=False, error="UNRECOGNIZED")

    except Exception as e:
        logger.error(f"Gemini recognition error: {e}")
        return VisionResult(recognized=False, error=str(e))
