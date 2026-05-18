"""Gemini LLM provider using the google-generativeai SDK."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import google.generativeai as genai

from services.ai.interfaces import BaseLLM
from core.config import settings

_LOGGER = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLM):
    """LLM implementation backed by Gemini models."""

    def __init__(self) -> None:
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
        genai.configure(api_key=api_key)

        model_candidates = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]

        self._model = None
        self._model_name = None

        try:
            available_models = [m.name for m in genai.list_models()]
        except Exception as e:
            _LOGGER.warning("Could not list available models: %s", e)
            available_models = []

        for model_name in model_candidates:
            full_name = model_name if model_name.startswith("models/") else f"models/{model_name}"
            if available_models and full_name not in available_models:
                continue
            try:
                self._model = genai.GenerativeModel(model_name)
                self._model_name = model_name
                _LOGGER.info("Initialized Gemini model: %s", model_name)
                break
            except Exception:
                continue

        if self._model is None:
            raise ValueError(f"Could not initialize any Gemini model. Tried: {model_candidates}")

    async def generate_response(self, prompt: str, context_data: str, lang: str) -> str:
        from utils.prompt_templates import build_voice_system_prompt

        system_instruction = build_voice_system_prompt(lang)
        full_prompt = (
            f"System Instruction:\n{system_instruction}\n\n"
            f"Context Data:\n{context_data}\n\n"
            f"User Prompt:\n{prompt}"
        )

        def _do_generate() -> Any:
            return self._model.generate_content(full_prompt)

        response = await asyncio.to_thread(_do_generate)
        text = getattr(response, "text", None)
        return text.strip() if text else ""
