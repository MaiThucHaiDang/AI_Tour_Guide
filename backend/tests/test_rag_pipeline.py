import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app
from services.voice.intro_service import intro_service

client = TestClient(app, raise_server_exceptions=False)

def test_intro_service_cache_retrieval():
    # Seed the cache manually for testing
    intro_service._cache["1:vi"] = [
        "Mô tả lịch sử về Ngọ Môn phong cách sử gia",
        "Mô tả kiến trúc về Ngọ Môn phong cách mỹ thuật",
        "Mô tả cung đình hoàng gia về Ngọ Môn đầy tôn nghiêm",
        "Mô tả hiện đại về Ngọ Môn phong cách khám phá trẻ trung"
    ]
    
    intro = intro_service.get_random_intro(1, "vi")
    assert intro in intro_service._cache["1:vi"]
    
    # Check invalid lang returns None
    assert intro_service.get_random_intro(1, "fr") is None

def test_unified_chat_out_of_scope():
    # Mock LLM generation and parsing
    with patch("services.llm.gemini_llm.GeminiLLMProvider.generate_response", new_callable=AsyncMock) as mock_gen, \
         patch("orchestrators.unified_orchestrator.UnifiedOrchestrator._parse_query", new_callable=AsyncMock) as mock_parse:
        
        mock_parse.return_value = {
            "intent": "out_of_scope",
            "entities": [],
            "question_type": "unknown",
            "needs_artifact_context": False,
            "needs_event_context": False,
            "resolved_subject": None
        }
        mock_gen.return_value = "Dạ, hiện tại dữ liệu thuyết minh của Đại Nội Huế chưa có thông tin về thời tiết Hà Nội."
        
        resp = client.post("/api/v1/chat/unified", data={
            "text": "Thời tiết ở Hà Nội hôm nay thế nào?",
            "lang": "vi"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "response_text" in data
        assert "Hà Nội" in data["response_text"]
        
def test_unified_chat_introduce_cached():
    # Seed cache
    intro_service._cache["8:vi"] = ["Điện Thái Hòa là cung điện thiết triều chính..."]
    
    # Mock parse query
    with patch("orchestrators.unified_orchestrator.UnifiedOrchestrator._parse_query", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = {
            "intent": "introduce",
            "entities": ["Điện Thái Hòa"],
            "question_type": "what",
            "needs_artifact_context": True,
            "needs_event_context": False,
            "resolved_subject": None
        }
        
        # Calling with text that triggers intro and matching ID
        resp = client.post("/api/v1/chat/unified", data={
            "text": "Giới thiệu ngắn gọn và hấp dẫn về Điện Thái Hòa",
            "lang": "vi",
            "artifact_id": 8
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["response_text"] == "Điện Thái Hòa là cung điện thiết triều chính..."
        # Should be answered from cache, avoiding LLM calls
        assert "cache" in data["answer_source"]
