"""Gemini LLM provider using the google-genai SDK."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from google import genai
from google.genai import errors as genai_errors

from services.ai.interfaces import BaseLLM
from core.config import get_settings

_LOGGER = logging.getLogger(__name__)

_RETRY_CODES = {500, 503}
_MAX_RETRIES = 1
_RETRY_BACKOFF = [1.0]


class GeminiLLMProvider(BaseLLM):
    """LLM implementation backed by Gemini models."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        label: str = "gemini",
    ) -> None:
        current_settings = get_settings()
        resolved_api_key = (api_key or current_settings.GEMINI_API_KEY).strip()
        if not resolved_api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")

        self._label = label
        self._model_name = (model_name or current_settings.GEMINI_TEXT_MODEL).strip() or "gemini-2.5-flash-lite"
        self._client = genai.Client(api_key=resolved_api_key)
        _LOGGER.info("Initialized Gemini model: %s (%s)", self._model_name, self._label)

    async def generate_response(
        self,
        prompt: str,
        context_data: str,
        lang: str,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        from utils.prompt_templates import build_voice_system_prompt

        system_instruction = system_prompt or build_voice_system_prompt(lang)
        current_settings = get_settings()
        
        contents = (
            f"Context Data:\n{context_data}\n\n"
            f"User Prompt:\n{prompt}"
        )

        effective_max_tokens = max_tokens or current_settings.LLM_MAX_TOKENS

        def _do_generate() -> Any:
            return self._client.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=current_settings.LLM_TEMPERATURE,
                    max_output_tokens=effective_max_tokens,
                )
            )

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = await asyncio.to_thread(_do_generate)
                text = getattr(response, "text", None)
                return text.strip() if text else ""
            except genai_errors.APIError as e:
                last_exc = e
                if e.code in _RETRY_CODES and attempt < _MAX_RETRIES:
                    delay = _RETRY_BACKOFF[attempt]
                    _LOGGER.warning(
                        "Gemini %s (attempt %d/%d), retrying in %.0fs...",
                        e.code, attempt + 1, _MAX_RETRIES + 1, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                last_exc = e
                # Treat transient network errors as retriable
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BACKOFF[attempt]
                    _LOGGER.warning(
                        "Gemini error (attempt %d/%d), retrying in %.0fs: %s",
                        attempt + 1, _MAX_RETRIES + 1, delay, e,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

    async def generate_response_stream(
        self, prompt: str, context_data: str, lang: str, system_prompt: str | None = None
    ):
        from utils.prompt_templates import build_voice_system_prompt

        system_instruction = system_prompt or build_voice_system_prompt(lang)
        current_settings = get_settings()
        
        contents = (
            f"Context Data:\n{context_data}\n\n"
            f"User Prompt:\n{prompt}"
        )

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = await self._client.aio.models.generate_content_stream(
                    model=self._model_name,
                    contents=contents,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=current_settings.LLM_TEMPERATURE,
                        max_output_tokens=current_settings.LLM_MAX_TOKENS,
                    )
                )
                async for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except genai_errors.APIError as e:
                last_exc = e
                if e.code in _RETRY_CODES and attempt < _MAX_RETRIES:
                    delay = _RETRY_BACKOFF[attempt]
                    _LOGGER.warning(
                        "Gemini stream %s (attempt %d/%d), retrying in %.0fs...",
                        e.code, attempt + 1, _MAX_RETRIES + 1, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BACKOFF[attempt]
                    _LOGGER.warning(
                        "Gemini stream error (attempt %d/%d), retrying in %.0fs: %s",
                        attempt + 1, _MAX_RETRIES + 1, delay, e,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
