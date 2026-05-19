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
from schemas.vision import VisionResult

class MockSTT(BaseSTT):
    async def transcribe(self, audio_bytes, filename=None, content_type=None, language_hint=None):
        return "Xin chào Ngọ Môn", "vi"

class MockLLM(BaseLLM):
    async def generate_response(self, prompt, context_data, lang):
        return f"AI Response to: {prompt}"

class MockTTS(BaseTTS):
    async def synthesize(self, text, lang):
        return b"mock_audio_bytes"

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
    
    assert result.response_text == "AI Response to: Chào bạn"
    assert result.audio_bytes == b"mock_audio_bytes"
    assert result.transcript == "Chào bạn"

@pytest.mark.asyncio
async def test_image_only_chat(orchestrator):
    # Mock vision and DB
    mock_vision = VisionResult(recognized=True, artifact_id="1", raw_label="Ngọ Môn")
    
    with patch("orchestrators.unified_orchestrator.recognize_image", AsyncMock(return_value=mock_vision)), \
         patch("orchestrators.unified_orchestrator.get_artifact_context_by_id", AsyncMock(return_value="Dữ liệu Ngọ Môn từ DB")):
        
        result = await orchestrator.process_chat_request(
            image_base64="mock_base64_data",
            lang="vi",
            session_id="test_session"
        )
        
        assert "Ngọ Môn" in result.transcript
        assert result.artifact_id == "1"
        assert result.artifact_name == "Ngọ Môn"
        assert result.response_text == "AI Response to: [User sent an image of Ngọ Môn]"

@pytest.mark.asyncio
async def test_multimodal_chat(orchestrator):
    # Mock vision and DB
    mock_vision = VisionResult(recognized=True, artifact_id="1", raw_label="Ngọ Môn")
    
    with patch("orchestrators.unified_orchestrator.recognize_image", AsyncMock(return_value=mock_vision)), \
         patch("orchestrators.unified_orchestrator.get_artifact_context_by_id", AsyncMock(return_value="Dữ liệu Ngọ Môn từ DB")):
        
        result = await orchestrator.process_chat_request(
            text_query="Cái này xây năm nào?",
            image_base64="mock_base64_data",
            lang="vi",
            session_id="test_session"
        )
        
        assert result.transcript == "Cái này xây năm nào?"
        assert result.artifact_id == "1"
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
    with patch.object(MockLLM, 'generate_response', AsyncMock(side_effect=lambda p, c, l: c)) as mock_gen:
        context = await orchestrator.process_chat_request(
            text_query="Tên tôi là gì?",
            session_id=session_id
        )
        
        assert "Tôi là Nam" in context.response_text
        assert "User: Tôi là Nam" in context.response_text
