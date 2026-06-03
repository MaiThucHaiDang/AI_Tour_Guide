"""Image recognition service using Gemini Vision.

Moved from: src/backend/services/image_recognition.py
Logic preserved exactly.
"""

from __future__ import annotations

import io
import json
import logging
import threading
import asyncio

from PIL import Image
from google import genai
from google.genai import types

from core.config import settings
from schemas.vision import VisionResult
from services.artifacts.label_mapping import map_vision_label_to_artifact_id
from repositories.artifact_repository import find_artifact_by_name
from utils.request_validation import decode_image_base64, validate_image_base64_size
from utils.image_utils import validate_and_preprocess_image, optimize_image_for_api, get_image_quality_estimate

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


async def recognize_image(image_base64: str, lang: str = "vi", lat: float = None, lng: float = None, _retry_count: int = 0) -> VisionResult:
    """Recognize an artifact from a base64-encoded image with GPS support.
    
    Args:
        image_base64: Base64 encoded image data
        lang: Language code ('vi' or 'en')
        lat: Optional latitude for GPS-based reranking
        lng: Optional longitude for GPS-based reranking
        _retry_count: Internal retry counter (do not set)
        
    Returns:
        VisionResult with recognition status and artifact data
    """
    try:
        validate_image_base64_size(image_base64)
        image_bytes = decode_image_base64(image_base64)
        
        # Validate and preprocess image
        try:
            image = validate_and_preprocess_image(image_bytes)
            if image is None:
                return VisionResult(recognized=False, error="INVALID_IMAGE")
        except ValueError as e:
            logger.warning("Image validation failed: %s", e)
            return VisionResult(recognized=False, error="INVALID_IMAGE")
        
        # Optimize image for API
        image = optimize_image_for_api(image)
        
        # Estimate image quality
        quality = get_image_quality_estimate(image)
        logger.debug("Image quality estimate: %.1f%%", quality)
        
        if quality < 30:
            logger.warning("Low image quality: %.1f%%", quality)
            # Still process but log the warning

        from utils.prompt_templates import build_vision_recognition_prompt
        prompt = build_vision_recognition_prompt(lang)

        try:
            response = await _get_vision_model().aio.models.generate_content(
                model=settings.GEMINI_VISION_MODEL,
                contents=[prompt, image],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
        except Exception as api_error:
            # Retry logic with exponential backoff for transient errors
            error_str = str(api_error).lower()
            is_retryable = (
                "429" in str(api_error) or  # Rate limit
                "500" in str(api_error) or  # Server error
                "timeout" in error_str or
                "temporarily" in error_str or
                "unavailable" in error_str
            )
            
            if _retry_count < 2 and is_retryable:
                wait_time = (2 ** _retry_count) * 0.5  # Exponential: 0.5s, 1s, 2s
                logger.warning("API error (retry %d/%d), waiting %.1fs: %s", _retry_count + 1, 2, wait_time, api_error)
                await asyncio.sleep(wait_time)
                return await recognize_image(image_base64, lang, lat, lng, _retry_count + 1)
            else:
                logger.error("Gemini API error after retries: %s", api_error, exc_info=True)
                # Return specific error based on API error
                if "401" in str(api_error) or "Unauthorized" in str(api_error):
                    return VisionResult(recognized=False, error="401")
                elif "429" in str(api_error):
                    return VisionResult(recognized=False, error="429")
                else:
                    return VisionResult(recognized=False, error="API_ERROR")
        
        raw_text = response.text
        if not raw_text:
            logger.warning("Gemini Vision returned empty/None response (possibly blocked by safety filter)")
            return VisionResult(recognized=False, error="VISION_EMPTY_RESPONSE")
        response_text = raw_text.strip()
        logger.debug("Gemini Vision raw response: %s", response_text)

        # Parse JSON response with robust error handling
        label = ""
        confidence = 0.0
        is_artifact = False
        visual_features = ""
        
        try:
            # Handle potential markdown code blocks in response
            clean_json = response_text
            if clean_json.startswith("```json"):
                clean_json = clean_json.split("```json", 1)[1].split("```", 1)[0].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json.split("```", 1)[1].split("```", 1)[0].strip()

            # Remove any trailing commas or invalid JSON
            clean_json = clean_json.rstrip(",")
            
            data = json.loads(clean_json)
            label = str(data.get("artifact_name", "")).strip()
            confidence = float(data.get("confidence", 0.0))
            is_artifact = bool(data.get("is_historical_artifact", False))
            visual_features = str(data.get("visual_features", "")).strip()

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning("Failed to parse JSON response from vision model: %s", e)
            # Fallback: if response contains UNKNOWN keyword, return not recognized
            if "UNKNOWN" in response_text.upper() or "KHÔNG BIẾT" in response_text.upper():
                return VisionResult(recognized=False, error="UNRECOGNIZED")
            # Otherwise try to extract text fallback
            label = response_text[:100].strip()
            confidence = 0.3
            is_artifact = False

        # Validation checks
        if not label or label.upper() == "UNKNOWN":
            logger.debug("Model returned UNKNOWN or empty label")
            return VisionResult(recognized=False, error="UNRECOGNIZED")
        
        if not is_artifact:
            logger.debug("Model classified as non-artifact: %s", label)
            return VisionResult(recognized=False, error="NOT_AN_ARTIFACT", confidence_score=confidence)
        
        if confidence < settings.VISION_CONFIDENCE_THRESHOLD:
            logger.warning("Low confidence (%.2f) for label: %s", confidence, label)
            return VisionResult(recognized=False, error="LOW_CONFIDENCE", confidence_score=confidence)

        # 1. Try dynamic database lookup (New Robust Way with GPS)
        try:
            artifact_info = await find_artifact_by_name(label, lat=lat, lng=lng)
            
            if artifact_info:
                logger.info("Successfully matched label '%s' to artifact_id '%s' with confidence %.2f", 
                           label, artifact_info.art_id, confidence)
                return VisionResult(
                    recognized=True,
                    raw_label=label,
                    artifact_id=artifact_info.art_id,
                    confidence_score=confidence,
                )
        except Exception as db_error:
            logger.warning("Database lookup failed: %s", db_error, exc_info=True)

        # 2. Try legacy mapping fallback (Hardcoded Aliases)
        try:
            artifact_id = map_vision_label_to_artifact_id(label)

            if artifact_id:
                logger.info("Matched label '%s' using legacy mapping to artifact_id '%s'", label, artifact_id)
                return VisionResult(
                    recognized=True,
                    raw_label=label,
                    artifact_id=artifact_id,
                    confidence_score=confidence,
                )
        except Exception as mapping_error:
            logger.warning("Legacy mapping lookup failed: %s", mapping_error, exc_info=True)

        logger.warning("Label '%s' not found in DB or mapping (confidence: %.2f)", label, confidence)
        return VisionResult(recognized=False, error="UNRECOGNIZED", confidence_score=confidence)

    except Exception as e:
        logger.error("Gemini recognition error: %s", e, exc_info=True)
        return VisionResult(recognized=False, error=str(e))
