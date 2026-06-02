"""Integration tests for the Unified Multimodal Chatbot Orchestrator.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from orchestrators.unified_orchestrator import UnifiedOrchestrator, UnifiedChatResult
from services.ai.interfaces import BaseLLM, BaseSTT, BaseTTS
from services.memory.conversation_memory import ConversationMemory
from schemas.vision import ArtifactInfo, VisionResult

class MockSTT(BaseSTT):
    async def transcribe(self, audio_bytes, filename=None, content_type=None, language_hint=None):
        return "Xin chào Ngọ Môn", "vi"

class MockLLM(BaseLLM):
    async def generate_response(self, prompt, context_data, lang):
        return f"AI Response to: {prompt}"

    async def generate_response_stream(self, prompt, context_data, lang):
        yield f"AI Response to: {prompt}"

class FailingLLM(BaseLLM):
    async def generate_response(self, prompt, context_data, lang):
        raise RuntimeError("provider unavailable")

    async def generate_response_stream(self, prompt, context_data, lang):
        raise RuntimeError("provider unavailable")

class MockTTS(BaseTTS):
    async def synthesize(self, text, lang):
        return b"mock_audio_bytes"


def sample_artifact() -> ArtifactInfo:
    return ArtifactInfo(
        art_id="1",
        loc_id="1",
        name_vi="Ngọ Môn",
        name_en="Ngo Mon Gate",
        history_text_vi=(
            "Ngọ Môn là cổng chính phía nam của Hoàng thành Huế. "
            "Công trình gắn với nhiều nghi lễ quan trọng của triều Nguyễn."
        ),
        history_text_en=(
            "Ngo Mon Gate is the main southern entrance of the Hue Imperial City. "
            "It is associated with major ceremonies of the Nguyen Dynasty."
        ),
        author="Minh Mang Emperor",
        year=1833,
    )

@pytest.fixture
def orchestrator():
    stt = MockSTT()
    llm = MockLLM()
    tts = MockTTS()
    memory = ConversationMemory()
    return UnifiedOrchestrator(stt, llm, tts, memory)

@pytest.mark.asyncio
async def test_text_only_chat(orchestrator):
    result = await orchestrator.process_chat_request(
        text_query="Chào bạn",
        lang="vi",
        session_id="test_session"
    )
    
    assert "Xin chào" in result.response_text
    assert result.answer_source == "template"
    assert result.audio_bytes is None
    assert result.transcript == "Chào bạn"

@pytest.mark.asyncio
async def test_image_only_chat(orchestrator):
    # Mock vision and DB
    mock_vision = VisionResult(recognized=True, artifact_id="999", raw_label="Ngọ Môn")
    
    with patch("orchestrators.unified_orchestrator.recognize_image", AsyncMock(return_value=mock_vision)), \
         patch("orchestrators.unified_orchestrator.get_artifact_by_id", AsyncMock(return_value=None)), \
         patch("orchestrators.unified_orchestrator.get_artifact_context_by_id", AsyncMock(return_value="Dữ liệu Ngọ Môn từ DB")):
        
        result = await orchestrator.process_chat_request(
            image_base64="mock_base64_data",
            lang="vi",
            session_id="test_session"
        )
        
        assert "Ngọ Môn" in result.transcript
        assert result.artifact_id == "999"
        assert result.artifact_name == "Ngọ Môn"
        assert result.response_text == "AI Response to: [User sent an image of Ngọ Môn]"

@pytest.mark.asyncio
async def test_multimodal_chat(orchestrator):
    # Mock vision and DB
    mock_vision = VisionResult(recognized=True, artifact_id="999", raw_label="Ngọ Môn")
    
    with patch("orchestrators.unified_orchestrator.recognize_image", AsyncMock(return_value=mock_vision)), \
         patch("orchestrators.unified_orchestrator.get_artifact_by_id", AsyncMock(return_value=None)), \
         patch("orchestrators.unified_orchestrator.get_artifact_context_by_id", AsyncMock(return_value="Dữ liệu Ngọ Môn từ DB")):
        
        result = await orchestrator.process_chat_request(
            text_query="Cái này xây năm nào?",
            image_base64="mock_base64_data",
            lang="vi",
            session_id="test_session"
        )
        
        assert result.transcript == "Cái này xây năm nào?"
        assert result.artifact_id == "999"
        assert "AI Response to: Cái này xây năm nào?" in result.response_text

@pytest.mark.asyncio
async def test_context_memory(orchestrator):
    session_id = "test_context_session"
    
    # First turn
    await orchestrator.process_chat_request(
        text_query="Tôi là Nam",
        session_id=session_id
    )
    
    # Second turn - check if memory is formatted correctly in the next call
    # We'll use a mock LLM to capture the context
    async def mock_gen_side_effect(p, c, l):
        return c

    with patch.object(MockLLM, 'generate_response', AsyncMock(side_effect=mock_gen_side_effect)) as mock_gen_call:
        context = await orchestrator.process_chat_request(
            text_query="Tên tôi là gì?",
            session_id=session_id
        )
        
        assert "Tôi là Nam" in context.response_text
        assert "User: Tôi là Nam" in context.response_text

@pytest.mark.asyncio
async def test_unknown_database_question_gets_resilient_fallback():
    orchestrator = UnifiedOrchestrator(
        MockSTT(),
        FailingLLM(),
        MockTTS(),
        ConversationMemory(),
    )

    with patch("orchestrators.unified_orchestrator.find_artifact_by_name", AsyncMock(return_value=None)), \
         patch("orchestrators.unified_orchestrator.get_artifact_context", AsyncMock(return_value="No matching artifact found in database.")):
        result = await orchestrator.process_chat_request(
            text_query="Hãy kể về một hiện vật chưa có trong dữ liệu",
            lang="vi",
            session_id="fallback_session",
        )

    assert "chưa có mục dữ liệu khớp" in result.response_text
    assert result.answer_source == "llm"
    assert result.transcript == "Hãy kể về một hiện vật chưa có trong dữ liệu"


@pytest.mark.asyncio
async def test_direct_fact_answer_avoids_llm():
    orchestrator = UnifiedOrchestrator(
        MockSTT(),
        FailingLLM(),
        MockTTS(),
        ConversationMemory(),
    )

    with patch(
        "orchestrators.unified_orchestrator.find_artifact_by_name",
        AsyncMock(return_value=sample_artifact()),
    ):
        result = await orchestrator.process_chat_request(
            text_query="Ngọ Môn được xây năm nào?",
            lang="vi",
            session_id="direct_fact_session",
        )

    assert "1833" in result.response_text
    assert result.answer_source == "db_direct"
    assert result.audio_bytes is None


@pytest.mark.asyncio
async def test_meaning_question_uses_stored_summary_without_llm():
    orchestrator = UnifiedOrchestrator(
        MockSTT(),
        FailingLLM(),
        MockTTS(),
        ConversationMemory(),
    )

    with patch(
        "orchestrators.unified_orchestrator.find_artifact_by_name",
        AsyncMock(return_value=sample_artifact()),
    ):
        result = await orchestrator.process_chat_request(
            text_query="Ý nghĩa lịch sử của Ngọ Môn là gì?",
            lang="vi",
            session_id="meaning_session",
        )

    assert "Ngọ Môn" in result.response_text
    assert "cổng chính" in result.response_text
    assert result.answer_source == "db_direct"
    assert result.audio_bytes is None
