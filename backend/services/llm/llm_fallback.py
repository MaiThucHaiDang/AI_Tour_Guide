"""Fallback LLM provider that tries multiple backends in order."""

from __future__ import annotations

import asyncio
import logging

from services.ai.interfaces import BaseLLM

_LOGGER = logging.getLogger(__name__)

_PER_PROVIDER_TIMEOUT = 10


class FallbackLLMProvider(BaseLLM):
    """Try each LLM provider in order until one succeeds."""

    def __init__(self, providers: list[BaseLLM]) -> None:
        if not providers:
            raise ValueError("At least one LLM provider is required.")
        self._providers = providers

    @staticmethod
    def _provider_label(provider: BaseLLM) -> str:
        return getattr(provider, "_label", type(provider).__name__)

    async def generate_response(
        self,
        prompt: str,
        context_data: str,
        lang: str,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        last_exc: Exception | None = None
        for provider in self._providers:
            provider_label = self._provider_label(provider)
            try:
                response = await asyncio.wait_for(
                    provider.generate_response(
                        prompt,
                        context_data,
                        lang,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                    ),
                    timeout=_PER_PROVIDER_TIMEOUT,
                )
                if not response.strip():
                    raise RuntimeError("Provider returned an empty response.")
                _LOGGER.info("LLM provider %s succeeded", provider_label)
                return response
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "LLM provider %s timed out after %ss",
                    provider_label, _PER_PROVIDER_TIMEOUT,
                )
                last_exc = TimeoutError(f"{provider_label} timed out")
            except Exception as exc:
                _LOGGER.warning(
                    "LLM provider %s failed: %s", provider_label, exc,
                )
                last_exc = exc
        raise RuntimeError("All LLM providers failed.") from last_exc

    async def generate_response_stream(
        self, prompt: str, context_data: str, lang: str, system_prompt: str | None = None
    ):
        """Try each LLM provider's streaming endpoint in order until one succeeds."""
        last_exc: Exception | None = None
        for provider in self._providers:
            provider_label = self._provider_label(provider)
            try:
                async for chunk in asyncio.wait_for(
                    provider.generate_response_stream(
                        prompt, context_data, lang, system_prompt=system_prompt
                    ),
                    timeout=_PER_PROVIDER_TIMEOUT,
                ):
                    yield chunk
                _LOGGER.info("LLM stream provider %s succeeded", provider_label)
                return  # success — stop trying other providers
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "LLM stream provider %s timed out after %ss",
                    provider_label, _PER_PROVIDER_TIMEOUT,
                )
                last_exc = TimeoutError(f"{provider_label} stream timed out")
            except Exception as exc:
                _LOGGER.warning(
                    "LLM stream provider %s failed: %s",
                    provider_label,
                    exc,
                )
                last_exc = exc
        raise RuntimeError("All LLM streaming providers failed.") from last_exc

