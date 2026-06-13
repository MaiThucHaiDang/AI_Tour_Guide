"""Integration tests for logic vulnerabilities, edge cases, and RAG robustness.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app
from services.map.game_service import game_service
from repositories.artifact_repository import canonicalize_transcript_entities, find_artifact_by_name
from orchestrators.unified_orchestrator import UnifiedOrchestrator
from services.memory.conversation_memory import ConversationMemory
from tests.test_unified_chatbot import MockSTT, MockTTS

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def cleanup_active_rooms():
    """Ensure game_service active rooms are cleared before/after each test."""
    game_service.active_rooms.clear()
    yield
    game_service.active_rooms.clear()


@pytest.fixture
def mock_llm():
    with patch("services.map.game_service.get_llm_provider") as mock_get:
        mock_provider = AsyncMock()
        mock_provider.generate_response.return_value = """
        {
          "questions": [
            {
              "question_text": "Điện Thái Hòa được xây dựng vào năm nào?",
              "options": ["1805", "1833", "1945", "1900"],
              "correct_option_index": 0,
              "explanation": "Điện Thái Hòa được khởi công xây dựng vào năm 1805 dưới triều vua Gia Long."
            },
            {
              "question_text": "Cửa Ngọ Môn có bao nhiêu lối đi?",
              "options": ["3 lối", "5 lối", "1 lối", "4 lối"],
              "correct_option_index": 1,
              "explanation": "Cửa Ngọ Môn có 5 lối đi, trong đó lối giữa dành cho vua."
            }
          ]
        }
        """
        mock_get.return_value = mock_provider
        yield mock_provider


@pytest.mark.asyncio
async def test_game_join_validation_vulnerabilities(mock_llm):
    """Test vulnerability controls for joining a game room: empty name, long name, bad code, duplicate name."""
    # 1. Create a valid room
    resp = client.post("/api/v1/game/create", json={"visited_ids": [8], "lang": "vi"})
    assert resp.status_code == 200
    room_code = resp.json()["room_code"]

    # 2. Try joining with empty nickname -> Should fail with 400
    resp_empty = client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "   "})
    assert resp_empty.status_code == 400
    assert "Biệt danh không được để trống" in resp_empty.json()["detail"]

    # 3. Try joining with extremely long nickname (>20 chars) -> Should fail with 400
    long_name = "A" * 25
    resp_long = client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": long_name})
    assert resp_long.status_code == 400
    assert "Biệt danh quá dài" in resp_long.json()["detail"]

    # 4. Try joining a non-existent room code -> Should fail with 400
    resp_bad_code = client.post("/api/v1/game/join", json={"room_code": "XYZW", "nickname": "An"})
    assert resp_bad_code.status_code == 400
    assert "Không tìm thấy phòng chơi" in resp_bad_code.json()["detail"]

    # 5. Join a player successfully
    resp_ok = client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "An"})
    assert resp_ok.status_code == 200

    # 6. Try joining with duplicate nickname -> Should fail with 400
    resp_dup = client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "An"})
    assert resp_dup.status_code == 400
    assert "Biệt danh này đã có người sử dụng" in resp_dup.json()["detail"]


@pytest.mark.asyncio
async def test_game_state_transition_vulnerabilities(mock_llm):
    """Test game logic transitions: start empty room, answer out of turn, double submit answer, start already started room."""
    # 1. Create room
    resp = client.post("/api/v1/game/create", json={"visited_ids": [8], "lang": "vi"})
    room_code = resp.json()["room_code"]

    # 2. Try starting the game without any players -> Should fail with 400
    resp_start_empty = client.post("/api/v1/game/start", json={"room_code": room_code})
    assert resp_start_empty.status_code == 400
    assert "Cần ít nhất 1 người chơi để bắt đầu" in resp_start_empty.json()["detail"]

    # 3. Add players
    client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "An"})
    client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "Binh"})

    # 4. Start the game successfully
    resp_start = client.post("/api/v1/game/start", json={"room_code": room_code})
    assert resp_start.status_code == 200
    assert resp_start.json()["room"]["status"] == "playing"

    # 5. Try starting the already started game -> Should fail with 400
    resp_start_again = client.post("/api/v1/game/start", json={"room_code": room_code})
    assert resp_start_again.status_code == 400
    assert "Phòng chơi đã bắt đầu" in resp_start_again.json()["detail"]

    # 6. Try submitting answer for question index = 1 while game is at question index = 0 -> Should fail with 400
    resp_wrong_idx = client.post("/api/v1/game/answer", json={
        "room_code": room_code,
        "nickname": "An",
        "question_index": 1,
        "selected_option": 0
    })
    assert resp_wrong_idx.status_code == 400
    assert "đã trôi qua hoặc chưa bắt đầu" in resp_wrong_idx.json()["detail"]

    # 7. Submit valid answer for question index = 0 -> Should succeed
    resp_ans = client.post("/api/v1/game/answer", json={
        "room_code": room_code,
        "nickname": "An",
        "question_index": 0,
        "selected_option": 0
    })
    assert resp_ans.status_code == 200

    # 8. Try double submitting answer for index = 0 -> Should fail with 400
    resp_dup_ans = client.post("/api/v1/game/answer", json={
        "room_code": room_code,
        "nickname": "An",
        "question_index": 0,
        "selected_option": 1
    })
    assert resp_dup_ans.status_code == 400
    assert "đã nộp đáp án cho câu hỏi này rồi" in resp_dup_ans.json()["detail"]


@pytest.mark.asyncio
async def test_rag_and_query_robustness():
    """Test fuzzy query matching and out-of-bounds fallbacks in RAG pipeline."""
    # 1. Accentless fuzzy matching test
    art = await find_artifact_by_name("dien kien trung")
    assert art is not None
    assert art.name_vi == "Điện Kiến Trung"

    # 2. Spell corrected query entity canonicalization
    corrected = await canonicalize_transcript_entities("gioi thieu ngo mon hue", "vi")
    assert "Ngọ Môn" in corrected
    assert "Huế" in corrected

    # 3. Out-of-bounds fallback general chat
    class MockLLMForGeneralChat:
        async def generate_response(self, prompt, context_data, lang, max_tokens=None, system_prompt=None):
            # Verify general chat context is passed if not matches
            if "GENERAL_CHAT" in context_data:
                return "Tôi chưa tìm thấy di tích này trong dữ liệu nội bộ."
            return "Ok"

    orchestrator = UnifiedOrchestrator(
        MockSTT(),
        MockLLMForGeneralChat(),
        MockTTS(),
        ConversationMemory(),
    )

    with patch("orchestrators.unified_orchestrator.find_artifact_by_name", AsyncMock(return_value=None)), \
         patch("orchestrators.unified_orchestrator.get_artifact_context", AsyncMock(return_value="No matching artifact")):
        result = await orchestrator.process_chat_request(
            text_query="Kể về Tháp Eiffel ở Pháp",
            lang="vi",
            session_id="test_oob"
        )
        assert "chưa tìm thấy" in result.response_text
