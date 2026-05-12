"""Fallback LLM provider that tries multiple backends in order."""

from __future__ import annotations

import logging

from services.voice.interfaces import BaseLLM


_LOGGER = logging.getLogger(__name__)


class FallbackLLMProvider(BaseLLM):
    """Try each LLM provider in order until one succeeds."""

    def __init__(self, providers: list[BaseLLM]) -> None:
        if not providers:
            raise ValueError("At least one LLM provider is required.")
        self._providers = providers

    async def generate_response(self, prompt: str, context_data: str, lang: str) -> str:
        last_exc: Exception | None = None
        for provider in self._providers:
            try:
                return await provider.generate_response(prompt, context_data, lang)
            except Exception as exc:
                _LOGGER.warning(
                    "LLM provider %s failed: %s",
                    type(provider).__name__,
                    exc,
                )
                last_exc = exc
        raise RuntimeError("All LLM providers failed.") from last_exc
