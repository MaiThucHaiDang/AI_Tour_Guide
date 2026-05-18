"""LLM response generation for recognized artifacts.

Moved from: src/backend/services/llm_orchestrator.py
"""

from __future__ import annotations

import logging

import google.generativeai as genai

from core.config import settings
from schemas.vision import ArtifactInfo, LLMResponse
from utils.prompt_templates import build_vision_system_prompt

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
_text_model = genai.GenerativeModel("gemini-flash-latest")


async def generate_response(
    artifact_data: ArtifactInfo,
    lang: str = "vi",
    user_question: str = "Hãy giới thiệu ngắn gọn về hiện vật này.",
) -> LLMResponse:
    """Generate a tour-guide response for a recognized artifact."""
    system_prompt = build_vision_system_prompt(artifact_data, lang)
    full_prompt = f"{system_prompt}\n\nCâu hỏi của khách tham quan: {user_question}"

    logger.info(f"Calling Gemini text for artifact: {artifact_data.art_id}")

    response = await _text_model.generate_content_async(full_prompt)
    response_text = response.text.strip()

    return LLMResponse(
        response_text=response_text,
        token_count=0,
        model_used="gemini-flash-latest",
    )
