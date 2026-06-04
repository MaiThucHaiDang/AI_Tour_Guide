import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app

client = TestClient(app, raise_server_exceptions=False)

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

def test_multiplayer_game_flow(mock_llm):
    # 1. Create room
    resp = client.post("/api/v1/game/create", json={"visited_ids": [8, 17], "lang": "vi"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    room_code = data["room_code"]
    assert len(room_code) == 4

    # 2. Join players
    resp1 = client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "An"})
    assert resp1.status_code == 200
    assert resp1.json()["success"] is True

    resp2 = client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "Binh"})
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True

    # Join duplicate name -> error
    resp3 = client.post("/api/v1/game/join", json={"room_code": room_code, "nickname": "An"})
    assert resp3.status_code == 400

    # 3. Get status in lobby
    status_resp = client.get(f"/api/v1/game/room/{room_code}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["room"]["status"] == "lobby"
    assert len(status_data["room"]["players"]) == 2

    # 4. Start game
    start_resp = client.post("/api/v1/game/start", json={"room_code": room_code})
    assert start_resp.status_code == 200
    assert start_resp.json()["success"] is True

    # 5. Submit answers
    ans_resp1 = client.post("/api/v1/game/answer", json={
        "room_code": room_code,
        "nickname": "An",
        "question_index": 0,
        "selected_option": 0
    })
    assert ans_resp1.status_code == 200
    assert ans_resp1.json()["is_correct"] is True
    assert ans_resp1.json()["score_awarded"] > 0

    ans_resp2 = client.post("/api/v1/game/answer", json={
        "room_code": room_code,
        "nickname": "Binh",
        "question_index": 0,
        "selected_option": 2
    })
    assert ans_resp2.status_code == 200
    assert ans_resp2.json()["is_correct"] is False
    assert ans_resp2.json()["score_awarded"] == 0

    # 6. Next to scoreboard
    next_resp = client.post("/api/v1/game/next", json={"room_code": room_code})
    assert next_resp.json()["room"]["status"] == "scoreboard"

    # 7. Next to question 1
    next_resp = client.post("/api/v1/game/next", json={"room_code": room_code})
    assert next_resp.json()["room"]["status"] == "playing"
    assert next_resp.json()["room"]["current_question_index"] == 1

def test_local_ip_endpoint():
    resp = client.get("/api/v1/game/local-ip")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "local_ip" in data
    assert len(data["local_ip"]) > 0
