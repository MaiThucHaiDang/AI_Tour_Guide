"""Gemini LLM provider using the google-genai SDK."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from google import genai

from services.ai.interfaces import BaseLLM
from core.config import get_settings

_LOGGER = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLM):
    """LLM implementation backed by Gemini models."""

    def __init__(self) -> None:
        current_settings = get_settings()
        api_key = current_settings.GEMINI_API_KEY.strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")

        self._model_name = current_settings.GEMINI_TEXT_MODEL.strip() or "gemini-2.0-flash"
        self._client = genai.Client(api_key=api_key)
        _LOGGER.info("Initialized Gemini model: %s", self._model_name)

    async def generate_response(self, prompt: str, context_data: str, lang: str) -> str:
        from utils.prompt_templates import build_voice_system_prompt

        system_instruction = build_voice_system_prompt(lang)
        current_settings = get_settings()
        
        full_prompt = (
            f"System Instruction:\n{system_instruction}\n\n"
            f"Context Data:\n{context_data}\n\n"
            f"User Prompt:\n{prompt}"
        )

        def _do_generate() -> Any:
            return self._client.models.generate_content(
                model=self._model_name,
                contents=full_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=current_settings.LLM_TEMPERATURE,
                    max_output_tokens=current_settings.LLM_MAX_TOKENS,
                )
            )

        response = await asyncio.to_thread(_do_generate)
        text = getattr(response, "text", None)
        return text.strip() if text else ""

    async def generate_response_stream(self, prompt: str, context_data: str, lang: str):
        from utils.prompt_templates import build_voice_system_prompt

        system_instruction = build_voice_system_prompt(lang)
        current_settings = get_settings()
        
        full_prompt = (
            f"System Instruction:\n{system_instruction}\n\n"
            f"Context Data:\n{context_data}\n\n"
            f"User Prompt:\n{prompt}"
        )

        response = await self._client.aio.models.generate_content_stream(
            model=self._model_name,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=current_settings.LLM_TEMPERATURE,
                max_output_tokens=current_settings.LLM_MAX_TOKENS,
            )
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text
