"""Tests for backend voice features."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from services.voice.groq_llm import GroqLLMProvider
from services.voice.interfaces import BaseLLM, BaseSTT, BaseTTS
from services.voice.language_manager import LanguageManager
from services.voice.voice_pipeline import VoiceOrchestrator


TEST_AUDIO = b"x" * 1200


class MockTTSProvider(BaseTTS):
    async def synthesize(self, text: str, lang: str) -> bytes:
        return text.encode("utf-8")


@pytest.mark.asyncio
async def test_unit_4_language_accuracy(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockLLMProvider(BaseLLM):
        def __init__(self) -> None:
            self.calls: list[dict[str, str]] = []

        async def generate_response(self, prompt: str, context_data: str, lang: str) -> str:
            self.calls.append({"prompt": prompt, "context_data": context_data, "lang": lang})
            if lang == "vi":
                return "Đây là câu trả lời ngắn gọn bằng tiếng Việt."
            return "This is a concise English answer."

    english_cases = [
        {
            "lang_param": "en",
            "transcript": f"Tell me about English artifact {index}",
            "expected_db_field": "history_text_en",
            "expected_tts_text": "This is a concise English answer.",
        }
        for index in range(1, 51)
    ]

    vietnamese_cases = [
        {
            "lang_param": "vi",
            "transcript": f"Hãy kể về hiện vật Việt Nam số {index}",
            "expected_db_field": "history_text_vi",
            "expected_tts_text": "Đây là câu trả lời ngắn gọn bằng tiếng Việt.",
        }
        for index in range(1, 51)
    ]

    all_cases = english_cases + vietnamese_cases
    assert len(english_cases) == 50
    assert len(vietnamese_cases) == 50
    assert len(all_cases) == 100

    for case in all_cases:
        class CaseSTTProvider(BaseSTT):
            async def transcribe(
                self,
                audio_bytes: bytes,
                filename: str | None = None,
                content_type: str | None = None,
                language_hint: str | None = None,
            ) -> tuple[str, str]:
                return case["transcript"], case["lang_param"]

        llm_provider = MockLLMProvider()
        orchestrator = VoiceOrchestrator(
            CaseSTTProvider(),
            llm_provider,
            MockTTSProvider(),
            db_lookup=lambda text, db_field: f"{db_field}::{text}",
        )

        result = await orchestrator.process_voice_request(TEST_AUDIO, case["lang_param"])
        result_text = result.audio_bytes.decode("utf-8")

        assert result_text == case["expected_tts_text"]
        assert llm_provider.calls[0]["lang"] == case["lang_param"]
        assert case["expected_db_field"] in llm_provider.calls[0]["context_data"]
        assert len(result_text.split()) < 100


@pytest.mark.asyncio
async def test_unit_5_language_switching() -> None:
    class SwitchingSTTProvider(BaseSTT):
        def __init__(self) -> None:
            self._calls = 0

        async def transcribe(
            self,
            audio_bytes: bytes,
            filename: str | None = None,
            content_type: str | None = None,
            language_hint: str | None = None,
        ) -> tuple[str, str]:
            self._calls += 1
            if self._calls == 1:
                return "Xin chào, kể về hiện vật này", "vi"
            return "Hello, now switch to English", "en"

    class SwitchingLLMProvider(BaseLLM):
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, str]] = []

        async def generate_response(self, prompt: str, context_data: str, lang: str) -> str:
            self.calls.append((prompt, context_data, lang))
            if lang == "vi":
                return "Đây là câu trả lời tiếng Việt cho lượt đầu."
            return "This is the English answer for the next turn."

    tts_provider = MockTTSProvider()
    llm_provider = SwitchingLLMProvider()
    stt_provider = SwitchingSTTProvider()

    orchestrator = VoiceOrchestrator(
        stt_provider,
        llm_provider,
        tts_provider,
        db_lookup=lambda text, db_field: f"{db_field}::{text}",
    )

    first_result = (
        await orchestrator.process_voice_request(TEST_AUDIO, "vi")
    ).audio_bytes.decode("utf-8")
    second_result = (
        await orchestrator.process_voice_request(TEST_AUDIO, "en")
    ).audio_bytes.decode("utf-8")

    assert first_result == "Đây là câu trả lời tiếng Việt cho lượt đầu."
    assert second_result == "This is the English answer for the next turn."
    assert [call[2] for call in llm_provider.calls] == ["vi", "en"]
    assert "history_text_vi" in llm_provider.calls[0][1]
    assert "history_text_en" in llm_provider.calls[1][1]


@pytest.mark.asyncio
async def test_groq_llm_provider_uses_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    provider = GroqLLMProvider()

    class _MockGroqResponse:
        choices = [type("Choice", (), {"message": type("Message", (), {"content": "OK"})()})()]

    async def _mock_create(**kwargs: object) -> _MockGroqResponse:
        return _MockGroqResponse()

    monkeypatch.setattr(provider._client.chat.completions, "create", _mock_create)

    result = await provider.generate_response("Prompt", "Context", "en")

    assert result == "OK"


def test_language_manager_maps_supported_languages() -> None:
    language_manager = LanguageManager()

    vi_context = language_manager.setup_context("vi")
    assert vi_context["db_field"] == "history_text_vi"
    assert vi_context["ui_locale"] == "vi-VN"

    en_context = language_manager.setup_context("en")
    assert en_context["db_field"] == "history_text_en"
    assert en_context["ui_locale"] == "en-US"