"""Tests for backend voice features.

Moved from: part4/backend/tests/test_voice_features.py
Updated import paths to match new project structure.
"""

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

from services.llm.groq_llm import GroqLLMProvider
from services.ai.interfaces import BaseLLM, BaseSTT, BaseTTS
from utils.language_manager import LanguageManager
from orchestrators.voice_orchestrator import VoiceOrchestrator

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
    assert len(all_cases) == 100

    for case in all_cases:
        class CaseSTTProvider(BaseSTT):
            async def transcribe(self, audio_bytes, filename=None, content_type=None, language_hint=None):
                return case["transcript"], case["lang_param"]

        llm_provider = MockLLMProvider()
        orchestrator = VoiceOrchestrator(
            CaseSTTProvider(), llm_provider, MockTTSProvider(),
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
        def __init__(self):
            self._calls = 0

        async def transcribe(self, audio_bytes, filename=None, content_type=None, language_hint=None):
            self._calls += 1
            if self._calls == 1:
                return "Xin chào, kể về hiện vật này", "vi"
            return "Hello, now switch to English", "en"

    class SwitchingLLMProvider(BaseLLM):
        def __init__(self):
            self.calls: list[tuple[str, str, str]] = []

        async def generate_response(self, prompt, context_data, lang):
            self.calls.append((prompt, context_data, lang))
            if lang == "vi":
                return "Đây là câu trả lời tiếng Việt cho lượt đầu."
            return "This is the English answer for the next turn."

    tts = MockTTSProvider()
    llm = SwitchingLLMProvider()
    stt = SwitchingSTTProvider()

    orchestrator = VoiceOrchestrator(
        stt, llm, tts,
        db_lookup=lambda text, db_field: f"{db_field}::{text}",
    )

    first = (await orchestrator.process_voice_request(TEST_AUDIO, "vi")).audio_bytes.decode("utf-8")
    second = (await orchestrator.process_voice_request(TEST_AUDIO, "en")).audio_bytes.decode("utf-8")

    assert first == "Đây là câu trả lời tiếng Việt cho lượt đầu."
    assert second == "This is the English answer for the next turn."
    assert [c[2] for c in llm.calls] == ["vi", "en"]


@pytest.mark.asyncio
async def test_groq_llm_provider_uses_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    from core.config import get_settings
    get_settings.cache_clear()

    provider = GroqLLMProvider()

    class _MockResponse:
        choices = [type("Choice", (), {"message": type("Message", (), {"content": "OK"})()})()]

    async def _mock_create(**kwargs):
        return _MockResponse()

    monkeypatch.setattr(provider._client.chat.completions, "create", _mock_create)
    result = await provider.generate_response("Prompt", "Context", "en")
    assert result == "OK"


def test_language_manager_maps_supported_languages() -> None:
    lm = LanguageManager()
    vi = lm.setup_context("vi")
    assert vi["db_field"] == "history_text_vi"
    assert vi["ui_locale"] == "vi-VN"
    en = lm.setup_context("en")
    assert en["db_field"] == "history_text_en"
    assert en["ui_locale"] == "en-US"
