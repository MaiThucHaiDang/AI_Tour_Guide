from __future__ import annotations

from types import SimpleNamespace

from core.config.settings import Settings
from services.ai.interfaces import BaseLLM


class DummyLLM(BaseLLM):
    def __init__(self, label: str, model_name: str | None = None) -> None:
        self._label = label
        self._model_name = model_name

    async def generate_response(
        self,
        prompt: str,
        context_data: str,
        lang: str,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        return ""

    async def generate_response_stream(
        self,
        prompt: str,
        context_data: str,
        lang: str,
        system_prompt: str | None = None,
    ):
        if False:
            yield ""


def test_gemini_api_key_list_deduplicates_in_order():
    settings = Settings(
        GEMINI_API_KEY="k1",
        GEMINI_API_KEY_2="k2",
        GEMINI_API_KEYS="k2, k3",
        GEMINI_TEXT_MODEL="m1",
        GEMINI_TEXT_MODEL_2="m2",
        GEMINI_TEXT_MODELS="m3",
    )

    assert settings.gemini_api_key_list == ["k1", "k2", "k3"]
    assert settings.gemini_text_model_list == ["m1", "m2", "m3"]


def test_get_llm_provider_expands_gemini_keys_before_groq(monkeypatch):
    from core import dependencies

    dependencies.get_llm_provider.cache_clear()
    monkeypatch.setattr(
        dependencies,
        "settings",
        SimpleNamespace(
            llm_provider_list=["gemini", "groq"],
            gemini_api_key_list=["k1", "k2"],
            gemini_text_model_list=["m1", "m2"],
        ),
    )
    monkeypatch.setattr(
        dependencies,
        "GeminiLLMProvider",
        lambda api_key=None, model_name=None, label="gemini": DummyLLM(label, model_name),
    )
    monkeypatch.setattr(dependencies, "GroqLLMProvider", lambda: DummyLLM("groq"))

    provider = dependencies.get_llm_provider()

    assert [item._label for item in provider._providers] == [
        "gemini_key_1",
        "gemini_key_2",
        "groq",
    ]
    assert [getattr(item, "_model_name", None) for item in provider._providers] == [
        "m1",
        "m2",
        None,
    ]
    dependencies.get_llm_provider.cache_clear()
