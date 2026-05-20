"""LLM response generation for recognized artifacts.

Moved from: src/backend/services/llm_orchestrator.py
"""

from __future__ import annotations

import logging

from google import genai

from core.config import settings
from schemas.vision import ArtifactInfo, LLMResponse
from utils.prompt_templates import build_vision_system_prompt

logger = logging.getLogger(__name__)

_text_client = None


def _get_text_client():
    global _text_client
    if _text_client is not None:
        return _text_client
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    _text_client = genai.Client(api_key=api_key)
    return _text_client


async def generate_response(
    artifact_data: ArtifactInfo,
    lang: str = "vi",
    user_question: str = "Hãy giới thiệu ngắn gọn về hiện vật này.",
) -> LLMResponse:
    """Generate a tour-guide response for a recognized artifact."""
    system_prompt = build_vision_system_prompt(artifact_data, lang)
    full_prompt = f"{system_prompt}\n\nCâu hỏi của khách tham quan: {user_question}"

    logger.info(f"Calling Gemini text for artifact: {artifact_data.art_id}")

    model_name = settings.GEMINI_TEXT_MODEL.strip() or "gemini-2.0-flash"
    response = await _get_text_client().aio.models.generate_content(
        model=model_name,
        contents=full_prompt,
    )
    response_text = response.text.strip()

    return LLMResponse(
        response_text=response_text,
        token_count=0,
        model_used=model_name,
    )
