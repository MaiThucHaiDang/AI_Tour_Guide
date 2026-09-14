"""Groq LLM provider using the Groq SDK with Llama 3 model."""

from __future__ import annotations

from groq import AsyncGroq

from services.ai.interfaces import BaseLLM
from core.config import get_settings


class GroqLLMProvider(BaseLLM):
    """LLM implementation backed by Groq's Llama 3 model."""

    def __init__(self, api_key: str | None = None, label: str = "groq") -> None:
        current_settings = get_settings()
        resolved_api_key = (api_key or current_settings.GROQ_API_KEY).strip()
        if not resolved_api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        self._label = label
        # Provider fallback is handled by FallbackLLMProvider. Disable SDK-level
        # retries so a throttled key does not delay the next configured key.
        self._client = AsyncGroq(api_key=resolved_api_key, max_retries=0)
        self._model = current_settings.GROQ_LLM_MODEL

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

        try:
            effective_max_tokens = max_tokens or current_settings.LLM_MAX_TOKENS
            message = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Context Data:\n{context_data}\n\nUser Prompt:\n{prompt}"},
                ],
                temperature=current_settings.LLM_TEMPERATURE,
                max_tokens=effective_max_tokens,
            )
            text = message.choices[0].message.content
            if text is None:
                return ""
            return text.strip()
        except Exception as exc:
            raise RuntimeError(f"Groq LLM request failed: {exc}") from exc

    async def generate_response_stream(
        self, prompt: str, context_data: str, lang: str, system_prompt: str | None = None
    ):
        from utils.prompt_templates import build_voice_system_prompt

        system_instruction = system_prompt or build_voice_system_prompt(lang)
        current_settings = get_settings()

        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Context Data:\n{context_data}\n\nUser Prompt:\n{prompt}"},
                ],
                temperature=current_settings.LLM_TEMPERATURE,
                max_tokens=current_settings.LLM_MAX_TOKENS,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            raise RuntimeError(f"Groq LLM streaming failed: {exc}") from exc

    @staticmethod
    def _limit_words(text: str, max_words: int) -> str:
        if not text:
            return ""
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]).strip()
