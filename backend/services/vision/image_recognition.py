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
from repositories.artifact_repository import find_artifact_by_name

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
_vision_model = genai.GenerativeModel(
    "gemini-flash-latest",
    generation_config={"response_mime_type": "application/json"}
)

CONFIDENCE_THRESHOLD = 0.6


async def recognize_image(image_base64: str, lang: str = "vi") -> VisionResult:
    """Recognize an artifact from a base64-encoded image."""
    try:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        from utils.prompt_templates import build_vision_recognition_prompt
        prompt = build_vision_recognition_prompt(lang)

        response = await _vision_model.generate_content_async(
            [prompt, image]
        )
        
        response_text = response.text.strip()
        logger.info(f"Gemini Vision raw response: {response_text}")

        # Basic failure detection
        if not response_text or "UNKNOWN" in response_text.upper() or "KHÔNG BIẾT" in response_text.upper():
            return VisionResult(recognized=False, error="UNRECOGNIZED")

        try:
            # Handle potential markdown code blocks in response
            clean_json = response_text
            if clean_json.startswith("```json"):
                clean_json = clean_json.split("```json", 1)[1].split("```", 1)[0].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json.split("```", 1)[1].split("```", 1)[0].strip()

            data = json.loads(clean_json)
            label = data.get("artifact_name", "")
            confidence = data.get("confidence", 0.0)
            is_artifact = data.get("is_historical_artifact", False)

            if not is_artifact or not label or label.upper() == "UNKNOWN":
                return VisionResult(recognized=False, error="NOT_AN_ARTIFACT")
            
            if confidence < CONFIDENCE_THRESHOLD:
                logger.warning(f"Low confidence ({confidence}) for label: {label}")
                return VisionResult(recognized=False, error="LOW_CONFIDENCE", confidence_score=confidence)

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response: {response_text}")
            # Minimal fallback if it's just a string (though response_mime_type should prevent this)
            label = response_text[:100]
            confidence = 0.5

        # 1. Try dynamic database lookup (New Robust Way)
        artifact_info = await find_artifact_by_name(label)
        
        if artifact_info:
            return VisionResult(
                recognized=True,
                raw_label=label,
                artifact_id=artifact_info.art_id,
                confidence_score=confidence,
            )

        # 2. Try legacy mapping fallback (Hardcoded Aliases)
        artifact_id = map_vision_label_to_artifact_id(label)

        if artifact_id:
            return VisionResult(
                recognized=True,
                raw_label=label,
                artifact_id=artifact_id,
                confidence_score=confidence,
            )

        logger.warning(f"Label '{label}' recognized by AI but not found in DB or mapping")
        return VisionResult(recognized=False, error="UNRECOGNIZED", confidence_score=confidence)

    except Exception as e:
        logger.error(f"Gemini recognition error: {e}", exc_info=True)
        return VisionResult(recognized=False, error=str(e))
