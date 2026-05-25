"""Image recognition service using Gemini Vision.

Moved from: src/backend/services/image_recognition.py
Logic preserved exactly.
"""

from __future__ import annotations

import io
import json
import logging
import threading

from PIL import Image
from google import genai
from google.genai import types

from core.config import settings
from schemas.vision import VisionResult
from services.artifacts.label_mapping import map_vision_label_to_artifact_id
from repositories.artifact_repository import find_artifact_by_name
from utils.request_validation import decode_image_base64, validate_image_base64_size

logger = logging.getLogger(__name__)

_vision_model = None
_vision_lock = threading.Lock()


def _get_vision_model():
    """Initialize Gemini Vision lazily so app startup stays local-demo friendly."""
    global _vision_model
    if _vision_model is not None:
        return _vision_model

    with _vision_lock:
        # Double-check after acquiring lock
        if _vision_model is not None:
            return _vision_model
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            raise RuntimeError("401: GEMINI_API_KEY is not configured.")
        _vision_model = genai.Client(api_key=api_key)
        return _vision_model


async def recognize_image(image_base64: str, lang: str = "vi", lat: float = None, lng: float = None) -> VisionResult:
    """Recognize an artifact from a base64-encoded image with GPS support."""
    try:
        validate_image_base64_size(image_base64)
        image_bytes = decode_image_base64(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        image = Image.open(io.BytesIO(image_bytes))

        from utils.prompt_templates import build_vision_recognition_prompt
        prompt = build_vision_recognition_prompt(lang)

        response = await _get_vision_model().aio.models.generate_content(
            model=settings.GEMINI_VISION_MODEL,
            contents=[prompt, image],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        
        raw_text = response.text
        if not raw_text:
            logger.warning("Gemini Vision returned empty/None response (possibly blocked by safety filter)")
            return VisionResult(recognized=False, error="VISION_EMPTY_RESPONSE")
        response_text = raw_text.strip()
        logger.debug("Gemini Vision raw response: %s", response_text)

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
            
            if confidence < settings.VISION_CONFIDENCE_THRESHOLD:
                logger.warning("Low confidence (%s) for label: %s", confidence, label)
                return VisionResult(recognized=False, error="LOW_CONFIDENCE", confidence_score=confidence)

        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response from vision model")
            # Minimal fallback if it's just a string (though response_mime_type should prevent this)
            label = response_text[:100]
            confidence = 0.5

        # 1. Try dynamic database lookup (New Robust Way with GPS)
        artifact_info = await find_artifact_by_name(label, lat=lat, lng=lng)
        
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

        logger.warning("Label '%s' recognized by AI but not found in DB or mapping", label)
        return VisionResult(recognized=False, error="UNRECOGNIZED", confidence_score=confidence)

    except Exception as e:
        logger.error("Gemini recognition error: %s", e, exc_info=True)
        return VisionResult(recognized=False, error=str(e))
