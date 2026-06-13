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
    async def generate_response(self, prompt, context_data, lang, max_tokens=None, system_prompt=None):
        return f"AI Response to: {prompt}"

    async def generate_response_stream(self, prompt, context_data, lang, system_prompt=None):
        yield f"AI Response to: {prompt}"

class FailingLLM(BaseLLM):
    async def generate_response(self, prompt, context_data, lang, max_tokens=None, system_prompt=None):
        raise RuntimeError("provider unavailable")

    async def generate_response_stream(self, prompt, context_data, lang, system_prompt=None):
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
    
    assert "Kính chào" in result.response_text
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
    async def mock_gen_side_effect(p, c, l, max_tokens=None, system_prompt=None):
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
        MockLLM(),
        MockTTS(),
        ConversationMemory(),
    )

    await orchestrator._memory.clear("direct_fact_session")

    with patch(
        "orchestrators.unified_orchestrator.find_artifact_by_name",
        AsyncMock(return_value=sample_artifact()),
    ), patch(
        "orchestrators.unified_orchestrator.get_artifact_by_id",
        AsyncMock(return_value=sample_artifact()),
    ):
        result = await orchestrator.process_chat_request(
            text_query="Ngọ Môn được xây năm nào?",
            lang="vi",
            session_id="direct_fact_session",
        )

    assert "Ngọ Môn được xây năm nào?" in result.response_text
    assert result.answer_source == "llm"
    assert result.audio_bytes is None  # TTS runs in background now
    assert result.tts_token is not None  # Token provided for frontend polling


@pytest.mark.asyncio
async def test_meaning_question_uses_stored_summary_without_llm():
    orchestrator = UnifiedOrchestrator(
        MockSTT(),
        MockLLM(),
        MockTTS(),
        ConversationMemory(),
    )

    await orchestrator._memory.clear("meaning_session")

    with patch(
        "orchestrators.unified_orchestrator.find_artifact_by_name",
        AsyncMock(return_value=sample_artifact()),
    ), patch(
        "orchestrators.unified_orchestrator.get_artifact_by_id",
        AsyncMock(return_value=sample_artifact()),
    ):
        result = await orchestrator.process_chat_request(
            text_query="Ý nghĩa lịch sử của Ngọ Môn là gì?",
            lang="vi",
            session_id="meaning_session",
        )

    assert "Ý nghĩa lịch sử của Ngọ Môn là gì?" in result.response_text
    assert result.answer_source == "llm"
    assert result.audio_bytes is None  # TTS runs in background now
    assert result.tts_token is not None  # Token provided for frontend polling


@pytest.mark.asyncio
async def test_context_intent_compare_keeps_primary(orchestrator):
    # Setup session memory with an active artifact (e.g. ID="1", Ngọ Môn)
    session_id = "test_compare_session"
    await orchestrator._memory.clear(session_id)
    
    # Store initial turn to establish active artifact ID="1"
    await orchestrator._memory.add_turn(
        session_id=session_id,
        role="assistant",
        content="Đây là Ngọ Môn.",
        context_data={"artifact_id": 1}
    )
    
    # Mock finding artifact "điện kiến trung" (different from current primary)
    comp_art = ArtifactInfo(
        art_id="2",
        loc_id="2",
        name_vi="Điện Kiến Trung",
        name_en="Kien Trung Palace",
        history_text_vi="Dữ liệu Điện Kiến Trung.",
        history_text_en="Kien Trung Palace data.",
        author="Khải Định Emperor",
        year=1923,
    )
    
    primary_art = sample_artifact()
    
    # Mock LLM to return COMPARE_OR_REFER for classification
    class MockIntentClassificationLLM(BaseLLM):
        def __init__(self):
            self.calls = []
            
        async def generate_response(self, prompt, context_data, lang, max_tokens=None, system_prompt=None):
            self.calls.append(prompt)
            if "phân loại" in prompt or "SWITCH" in prompt:
                return "COMPARE_OR_REFER"
            return f"Answer with context: {context_data}"

        async def generate_response_stream(self, prompt, context_data, lang, system_prompt=None):
            yield "stream"

    mock_llm = MockIntentClassificationLLM()
    orchestrator._llm = mock_llm

    with patch("orchestrators.unified_orchestrator.find_artifact_by_name", AsyncMock(return_value=comp_art)), \
         patch("orchestrators.unified_orchestrator.get_artifact_by_id", AsyncMock(return_value=primary_art)):
        
        result = await orchestrator.process_chat_request(
            text_query="Ngọ Môn với Điện Kiến Trung cái nào xây trước?",
            lang="vi",
            session_id=session_id
        )
        
        # Verify the primary artifact remains unchanged (1)
        assert result.artifact_id == 1
        assert result.artifact_name == "Ngọ Môn"
        # Verify both contexts are present in the db_context (which was passed to LLM)
        assert "DB_CONTEXT_PRIMARY (Ngọ Môn)" in result.response_text
        assert "DB_CONTEXT_COMPARATIVE (Điện Kiến Trung)" in result.response_text


@pytest.mark.asyncio
async def test_context_intent_switch_updates_primary(orchestrator):
    # Setup session memory with an active artifact (e.g. ID="1", Ngọ Môn)
    session_id = "test_switch_session"
    await orchestrator._memory.clear(session_id)
    
    await orchestrator._memory.add_turn(
        session_id=session_id,
        role="assistant",
        content="Đây là Ngọ Môn.",
        context_data={"artifact_id": 1}
    )
    
    # Mock finding artifact "điện kiến trung" (different from current primary)
    comp_art = ArtifactInfo(
        art_id="2",
        loc_id="2",
        name_vi="Điện Kiến Trung",
        name_en="Kien Trung Palace",
        history_text_vi="Dữ liệu Điện Kiến Trung.",
        history_text_en="Kien Trung Palace data.",
        author="Khải Định Emperor",
        year=1923,
    )
    
    primary_art = sample_artifact()
    
    # Mock LLM to return SWITCH for classification
    class MockSwitchClassificationLLM(BaseLLM):
        def __init__(self):
            self.calls = []
            
        async def generate_response(self, prompt, context_data, lang, max_tokens=None, system_prompt=None):
            self.calls.append(prompt)
            if "phân loại" in prompt or "SWITCH" in prompt:
                return "SWITCH"
            return f"Answer with context: {context_data}"

        async def generate_response_stream(self, prompt, context_data, lang, system_prompt=None):
            yield "stream"

    mock_llm = MockSwitchClassificationLLM()
    orchestrator._llm = mock_llm

    with patch("orchestrators.unified_orchestrator.find_artifact_by_name", AsyncMock(return_value=comp_art)), \
         patch("orchestrators.unified_orchestrator.get_artifact_by_id", AsyncMock(return_value=primary_art)):
        
        result = await orchestrator.process_chat_request(
            text_query="Dẫn tôi tới Điện Kiến Trung đi",
            lang="vi",
            session_id=session_id
        )
        
        # Verify the primary artifact is updated to "2"
        assert result.artifact_id == "2"
        assert result.artifact_name == "Điện Kiến Trung"
        assert "Name: Điện Kiến Trung" in result.response_text
        assert "DB_CONTEXT_PRIMARY" not in result.response_text
