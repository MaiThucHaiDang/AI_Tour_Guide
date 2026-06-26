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
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

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
_vision_clients: dict[str, Any] = {}
_vision_lock = threading.Lock()
_FEATURES_PATH = Path(__file__).resolve().parents[2] / "data" / "vision_artifact_features.json"
_DETAIL_RECOGNITION_TYPES = {"architectural_detail", "interior_detail", "museum_object"}


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


def _get_vision_providers() -> list[tuple[str, Any]]:
    """Return configured Gemini vision clients in fallback order."""
    api_keys = getattr(settings, "gemini_api_key_list", None)
    if api_keys is None:
        api_keys = [
            key.strip()
            for key in (
                getattr(settings, "GEMINI_API_KEY", ""),
                getattr(settings, "GEMINI_API_KEY_2", ""),
            )
            if key.strip()
        ]

    if not api_keys:
        raise RuntimeError("401: GEMINI_API_KEY is not configured.")

    providers: list[tuple[str, Any]] = []
    with _vision_lock:
        for index, api_key in enumerate(api_keys, start=1):
            if api_key not in _vision_clients:
                _vision_clients[api_key] = genai.Client(api_key=api_key)
            providers.append((f"gemini_key_{index}", _vision_clients[api_key]))
    return providers


async def _generate_vision_content(prompt: str, image: Any):
    """Call Gemini Vision, falling back to the next API key with the same model."""
    providers = _get_vision_providers()
    model_name = settings.GEMINI_VISION_MODEL
    last_error: Exception | None = None

    for provider_label, client in providers:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=[prompt, image],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            logger.info("Vision provider %s succeeded with model %s", provider_label, model_name)
            return response
        except Exception as api_error:
            last_error = api_error
            logger.warning(
                "Vision provider %s failed with model %s: %s",
                provider_label,
                model_name,
                api_error,
            )

    raise last_error or RuntimeError("Vision provider failed.")


@lru_cache(maxsize=1)
def _load_feature_catalog() -> dict[str, dict[str, Any]]:
    """Load normalized visual feature metadata for post-vision reranking."""
    try:
        with open(_FEATURES_PATH, "r", encoding="utf-8") as feature_file:
            rows = json.load(feature_file)
    except Exception as exc:
        logger.warning("Failed to load vision feature catalog: %s", exc)
        return {}

    catalog: dict[str, dict[str, Any]] = {}
    for item in rows if isinstance(rows, list) else []:
        if not isinstance(item, dict):
            continue
        artifact_id = str(item.get("artifact_id", "")).strip()
        if artifact_id:
            catalog[artifact_id] = item
    return catalog


def _normalize_text(text: Any) -> str:
    if text is None:
        return ""
    cleaned = str(text).replace("đ", "d").replace("Đ", "d")
    normalized = unicodedata.normalize("NFD", cleaned)
    stripped = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    stripped = re.sub(r"[^a-zA-Z0-9\s]", " ", stripped)
    return " ".join(stripped.lower().split())


def _coerce_feature_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in re.split(r"[,;]\s*", value) if part.strip()]
    return []


def _coerce_candidates(
    data: dict[str, Any],
    label: str,
    confidence: float,
    visual_features: str,
    image_context_description: str = "",
) -> list[dict[str, Any]]:
    raw_candidates = data.get("top_candidates")
    candidates: list[dict[str, Any]] = []
    if isinstance(raw_candidates, list):
        for raw in raw_candidates[:5]:
            if not isinstance(raw, dict):
                continue
            candidate_name = str(raw.get("artifact_name", "")).strip()
            if not candidate_name or candidate_name.upper() == "UNKNOWN":
                continue
            try:
                candidate_confidence = float(raw.get("confidence", 0.0))
            except (TypeError, ValueError):
                candidate_confidence = 0.0
            candidates.append({
                "artifact_name": candidate_name,
                "confidence": max(0.0, min(1.0, candidate_confidence)),
                "visible_features": _coerce_feature_list(raw.get("visible_features") or raw.get("matched_features")),
                "evidence": str(raw.get("evidence", "")).strip(),
            })

    if label and label.upper() != "UNKNOWN" and not any(
        _normalize_text(item.get("artifact_name")) == _normalize_text(label) for item in candidates
    ):
        candidates.insert(0, {
            "artifact_name": label,
            "confidence": max(0.0, min(1.0, confidence)),
            "visible_features": _coerce_feature_list(data.get("visible_features")) or _coerce_feature_list(visual_features),
            "evidence": image_context_description or str(data.get("visual_summary", "")).strip(),
        })
    return candidates[:5]


def _feature_terms_for(item: dict[str, Any], recognition_type: str) -> list[str]:
    fields = ["whole_building_features", "architectural_details", "interior_details", "museum_or_object_details"]
    if recognition_type in _DETAIL_RECOGNITION_TYPES:
        fields = ["architectural_details", "interior_details", "museum_or_object_details", "whole_building_features"]
    terms: list[str] = []
    for field in fields:
        terms.extend(_coerce_feature_list(item.get(field)))
    return terms


def _name_alias_match_score(artifact_info: Any, feature_item: dict[str, Any] | None, candidate_name: str) -> float:
    candidate_norm = _normalize_text(candidate_name)
    names = [
        getattr(artifact_info, "name_vi", ""),
        getattr(artifact_info, "name_en", ""),
    ]
    if feature_item:
        names.extend(_coerce_feature_list(feature_item.get("aliases_vi")))
        names.extend(_coerce_feature_list(feature_item.get("aliases_en")))
        names.append(feature_item.get("name_vi", ""))
        names.append(feature_item.get("name_en", ""))

    for name in names:
        name_norm = _normalize_text(name)
        if not name_norm:
            continue
        if candidate_norm == name_norm:
            return 1.0
        if candidate_norm in name_norm or name_norm in candidate_norm:
            return 0.85

    candidate_tokens = set(candidate_norm.split())
    best_overlap = 0.0
    for name in names:
        name_tokens = set(_normalize_text(name).split())
        if not candidate_tokens or not name_tokens:
            continue
        overlap = len(candidate_tokens & name_tokens) / max(len(candidate_tokens), len(name_tokens), 1)
        best_overlap = max(best_overlap, overlap)
    return min(0.75, best_overlap)


def _visual_feature_score(feature_item: dict[str, Any] | None, candidate: dict[str, Any], recognition_type: str) -> float:
    if not feature_item:
        return 0.0
    visible = " ".join(_coerce_feature_list(candidate.get("visible_features")) + [candidate.get("evidence", "")])
    visible_norm = _normalize_text(visible)
    if not visible_norm:
        return 0.0
    terms = [_normalize_text(term) for term in _feature_terms_for(feature_item, recognition_type)]
    terms = [term for term in terms if term]
    if not terms:
        return 0.0
    matches = 0
    for term in terms:
        term_tokens = term.split()
        if term in visible_norm or any(token in visible_norm for token in term_tokens if len(token) >= 4):
            matches += 1
    return min(1.0, matches / max(min(len(terms), 5), 1))


def _gps_score(lat: float | None, lng: float | None) -> float:
    if lat is None or lng is None:
        return 0.5
    return 1.0


def _final_candidate_score(
    candidate: dict[str, Any],
    artifact_info: Any,
    feature_item: dict[str, Any] | None,
    recognition_type: str,
    lat: float | None,
    lng: float | None,
) -> float:
    vision_confidence = max(0.0, min(1.0, float(candidate.get("confidence") or 0.0)))
    alias_score = _name_alias_match_score(artifact_info, feature_item, candidate.get("artifact_name", ""))
    feature_score = _visual_feature_score(feature_item, candidate, recognition_type)
    gps = _gps_score(lat, lng)

    if recognition_type in _DETAIL_RECOGNITION_TYPES:
        score = (
            vision_confidence * 0.35
            + alias_score * 0.20
            + feature_score * 0.35
            + gps * 0.10
        )
    else:
        score = (
            vision_confidence * 0.40
            + alias_score * 0.25
            + feature_score * 0.20
            + gps * 0.15
        )
    return round(max(0.0, min(1.0, score)), 3)


async def _match_best_candidate(
    candidates: list[dict[str, Any]],
    recognition_type: str,
    lat: float | None,
    lng: float | None,
) -> tuple[Any | None, str | None, float, list[dict[str, Any]]]:
    catalog = _load_feature_catalog()
    scored_candidates: list[dict[str, Any]] = []
    best_info = None
    best_score = -1.0
    best_label = None

    for candidate in candidates:
        label = candidate.get("artifact_name", "")
        artifact_info = None
        try:
            artifact_info = await find_artifact_by_name(label, lat=lat, lng=lng)
        except Exception as db_error:
            logger.warning("Database lookup failed for candidate '%s': %s", label, db_error)

        mapped_id = None
        if not artifact_info:
            try:
                mapped_id = map_vision_label_to_artifact_id(label)
                if mapped_id:
                    artifact_info = await find_artifact_by_name(label, lat=lat, lng=lng)
            except Exception as mapping_error:
                logger.warning("Legacy mapping lookup failed for candidate '%s': %s", label, mapping_error)

        if not artifact_info and mapped_id:
            candidate_score = round(float(candidate.get("confidence") or 0.0), 3)
            scored_candidates.append({
                **candidate,
                "artifact_id": str(mapped_id),
                "final_score": candidate_score,
            })
            if candidate_score > best_score:
                best_info = None
                best_label = label
                best_score = candidate_score
            continue

        if not artifact_info:
            scored_candidates.append({**candidate, "artifact_id": None, "final_score": 0.0})
            continue

        feature_item = catalog.get(str(artifact_info.art_id))
        candidate_score = _final_candidate_score(
            candidate, artifact_info, feature_item, recognition_type, lat, lng
        )
        scored_candidates.append({
            **candidate,
            "artifact_id": str(artifact_info.art_id),
            "final_score": candidate_score,
        })
        if candidate_score > best_score:
            best_info = artifact_info
            best_label = label
            best_score = candidate_score

    return best_info, best_label, max(0.0, best_score), scored_candidates


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
            response = await _generate_vision_content(prompt, image)
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
                    return VisionResult(recognized=False, error="VISION_AUTH_ERROR")
                elif "429" in str(api_error):
                    return VisionResult(recognized=False, error="VISION_RATE_LIMITED")
                elif "503" in str(api_error) or "unavailable" in error_str or "high demand" in error_str:
                    return VisionResult(recognized=False, error="VISION_PROVIDER_UNAVAILABLE")
                else:
                    return VisionResult(recognized=False, error="VISION_API_ERROR")
        
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
        recognition_type = "unknown"
        visual_summary = ""
        image_context_description = ""
        needs_user_confirmation = False
        candidates: list[dict[str, Any]] = []
        
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
            recognition_type = str(data.get("recognition_type", "unknown")).strip() or "unknown"
            visual_summary = str(data.get("visual_summary", "")).strip()
            image_context_description = str(data.get("image_context_description", "")).strip()
            if not image_context_description:
                image_context_description = visual_summary
            visible_features = _coerce_feature_list(data.get("visible_features"))
            visual_features = str(data.get("visual_features", "")).strip()
            if not visual_features and visible_features:
                visual_features = ", ".join(visible_features)
            needs_user_confirmation = bool(data.get("needs_user_confirmation", False))
            candidates = _coerce_candidates(data, label, confidence, visual_features, image_context_description)

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning("Failed to parse JSON response from vision model: %s", e)
            # Fallback: if response contains UNKNOWN keyword, return not recognized
            if "UNKNOWN" in response_text.upper() or "KHÔNG BIẾT" in response_text.upper():
                return VisionResult(recognized=False, error="UNRECOGNIZED")
            # Otherwise try to extract text fallback
            label = response_text[:100].strip()
            confidence = 0.3
            is_artifact = False
            candidates = []

        # Validation checks
        if not label or label.upper() == "UNKNOWN":
            logger.debug("Model returned UNKNOWN or empty label")
            return VisionResult(
                recognized=False,
                error="UNRECOGNIZED",
                confidence_score=confidence,
                recognition_type=recognition_type,
                visual_features=visual_features,
                visual_summary=visual_summary,
                image_context_description=image_context_description,
                top_candidates=candidates,
                needs_user_confirmation=needs_user_confirmation,
            )
        
        if not is_artifact:
            logger.debug("Model classified as non-artifact: %s", label)
            return VisionResult(
                recognized=False,
                error="NOT_AN_ARTIFACT",
                confidence_score=confidence,
                recognition_type=recognition_type,
                visual_features=visual_features,
                visual_summary=visual_summary,
                image_context_description=image_context_description,
                top_candidates=candidates,
                needs_user_confirmation=needs_user_confirmation,
            )
        
        if confidence < settings.VISION_CONFIDENCE_THRESHOLD:
            logger.warning("Low confidence (%.2f) for label: %s", confidence, label)
            return VisionResult(
                recognized=False,
                error="LOW_CONFIDENCE",
                confidence_score=confidence,
                recognition_type=recognition_type,
                visual_features=visual_features,
                visual_summary=visual_summary,
                image_context_description=image_context_description,
                top_candidates=candidates,
                needs_user_confirmation=True,
            )

        if not candidates:
            candidates = [{
                "artifact_name": label,
                "confidence": confidence,
                "visible_features": _coerce_feature_list(visual_features),
                "evidence": image_context_description or visual_summary,
            }]

        artifact_info, best_label, final_score, scored_candidates = await _match_best_candidate(
            candidates, recognition_type, lat, lng
        )

        if artifact_info:
            should_confirm = needs_user_confirmation or (
                final_score < 0.6 or (final_score < 0.7 and confidence < 0.9)
            )
            logger.info(
                "Successfully matched label '%s' to artifact_id '%s' with confidence %.2f final_score %.2f",
                best_label or label, artifact_info.art_id, confidence, final_score,
            )
            return VisionResult(
                recognized=True,
                raw_label=best_label or label,
                artifact_id=artifact_info.art_id,
                confidence_score=confidence,
                recognition_type=recognition_type,
                visual_features=visual_features,
                visual_summary=visual_summary,
                image_context_description=image_context_description,
                top_candidates=scored_candidates,
                needs_user_confirmation=should_confirm,
                final_score=final_score,
            )

        # Legacy mapping fallback can still resolve labels even if DB fuzzy search did not.
        try:
            artifact_id = map_vision_label_to_artifact_id(best_label or label)

            if artifact_id:
                should_confirm = needs_user_confirmation or (
                    final_score < 0.6 or (final_score < 0.7 and confidence < 0.9)
                )
                logger.info("Matched label '%s' using legacy mapping to artifact_id '%s'", best_label or label, artifact_id)
                return VisionResult(
                    recognized=True,
                    raw_label=best_label or label,
                    artifact_id=artifact_id,
                    confidence_score=confidence,
                    recognition_type=recognition_type,
                    visual_features=visual_features,
                    visual_summary=visual_summary,
                    image_context_description=image_context_description,
                    top_candidates=scored_candidates,
                    needs_user_confirmation=should_confirm,
                    final_score=final_score if final_score > 0 else confidence,
                )
        except Exception as mapping_error:
            logger.warning("Legacy mapping lookup failed: %s", mapping_error, exc_info=True)

        logger.warning("Label '%s' not found in DB or mapping (confidence: %.2f)", label, confidence)
        return VisionResult(
            recognized=False,
            error="UNRECOGNIZED",
            confidence_score=confidence,
            recognition_type=recognition_type,
            visual_features=visual_features,
            visual_summary=visual_summary,
            image_context_description=image_context_description,
            top_candidates=scored_candidates,
            needs_user_confirmation=True,
            final_score=final_score,
        )

    except Exception as e:
        logger.error("Gemini recognition error: %s", e, exc_info=True)
        return VisionResult(recognized=False, error=str(e))
