"""FastAPI dependency injection providers."""

from __future__ import annotations
import logging
from functools import lru_cache

from core.config import settings
from services.ai.interfaces import BaseLLM
from services.llm.gemini_llm import GeminiLLMProvider
from services.llm.groq_llm import GroqLLMProvider
from services.llm.llm_fallback import FallbackLLMProvider
from services.voice.groq_stt import GroqSTTProvider
from services.voice.edge_tts_provider import EdgeTTSProvider
from services.memory.conversation_memory import ConversationMemory

_logger = logging.getLogger(__name__)


@lru_cache()
def get_stt_provider() -> GroqSTTProvider:
    return GroqSTTProvider()


@lru_cache()
def get_tts_provider() -> EdgeTTSProvider:
    return EdgeTTSProvider()


@lru_cache()
def get_conversation_memory() -> ConversationMemory:
    return ConversationMemory()


@lru_cache()
def get_llm_provider() -> BaseLLM:
    """Build LLM provider chain based on configuration order."""
    errors: list[str] = []
    providers: list[BaseLLM] = []

    for name in settings.llm_provider_list:
        try:
            if name == "groq":
                providers.append(GroqLLMProvider())
            elif name == "gemini":
                gemini_keys = settings.gemini_api_key_list
                if not gemini_keys:
                    raise ValueError("GEMINI_API_KEY is not set in environment variables.")
                gemini_models = settings.gemini_text_model_list
                for index, api_key in enumerate(gemini_keys, start=1):
                    model_name = gemini_models[min(index - 1, len(gemini_models) - 1)]
                    providers.append(
                        GeminiLLMProvider(
                            api_key=api_key,
                            model_name=model_name,
                            label=f"gemini_key_{index}",
                        )
                    )
            else:
                errors.append(f"Unknown provider '{name}'")
        except Exception as exc:
            _logger.warning("LLM provider %s init failed: %s", name, exc)
            errors.append(f"{name}: {exc}")

    if not providers:
        raise ValueError("No LLM provider available. " + "; ".join(errors))

    if len(providers) == 1:
        return providers[0]
    return FallbackLLMProvider(providers)
