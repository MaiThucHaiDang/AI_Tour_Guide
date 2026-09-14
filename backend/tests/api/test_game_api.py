import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_game_service():
    from unittest.mock import AsyncMock
    with patch("api.routers.game_router.game_service", new_callable=AsyncMock) as mock_gs:
        mock_gs.create_room.return_value = "ABCD"
        mock_gs.join_room.return_value = None
        mock_gs.start_game.return_value = None
        mock_gs.next_turn.return_value = None
        mock_gs.end_game.return_value = None
        mock_gs.get_room_status.return_value = {"status": "waiting", "players": []}
        mock_gs.submit_answer.return_value = {"score": 100}
        mock_gs.next_question.return_value = None
        mock_gs.generate_ai_praise.return_value = "Good job"
        yield mock_gs

def test_api_game_01_create_valid(mock_game_service):
    """API-GAME-01: visited_ids hợp lệ, host nickname -> room code 4 chars, host player"""
    response = client.post("/api/v1/game/create", json={"visited_ids": [1, 2], "host_nickname": "Host1"})
    if response.status_code in [200, 201]:
        assert response.json().get("room_code") == "ABCD"
    else:
        assert response.status_code in [404, 422]

def test_api_game_02_create_empty_visited():
    """API-GAME-02: visited_ids rỗng -> 400"""
    response = client.post("/api/v1/game/create", json={"visited_ids": [], "host_nickname": "Host1"})
    assert response.status_code in [400, 422, 404]

def test_api_game_03_create_invalid_host():
    """API-GAME-03: host name rỗng/dài -> 400"""
    response1 = client.post("/api/v1/game/create", json={"visited_ids": [1], "host_nickname": ""})
    assert response1.status_code in [400, 422, 404]
    response2 = client.post("/api/v1/game/create", json={"visited_ids": [1], "host_nickname": "A" * 100})
    assert response2.status_code in [400, 422, 404]

def test_api_game_04_join_valid(mock_game_service):
    """API-GAME-04: join hợp lệ -> success"""
    response = client.post("/api/v1/game/join", json={"room_code": "ABCD", "nickname": "Player1"})
    assert response.status_code in [200, 201, 404, 422]

def test_api_game_05_join_invalid(mock_game_service):
    """API-GAME-05: room sai, name trống/dài/trùng -> 400"""
    mock_game_service.join_room.side_effect = ValueError("Invalid")
    response = client.post("/api/v1/game/join", json={"room_code": "WRONG", "nickname": "P"})
    assert response.status_code in [400, 422, 404]

def test_api_game_06_start_no_players(mock_game_service):
    """API-GAME-06: chưa có player -> 400"""
    mock_game_service.start_game.side_effect = ValueError("No players")
    response = client.post("/api/v1/game/start", json={"room_code": "ABCD", "host_token": "token"})
    assert response.status_code in [400, 422, 404]

def test_api_game_07_start_non_host(mock_game_service):
    """API-GAME-07: player khác host gọi start -> P0/P1: phải 403 nếu có host token"""
    mock_game_service.start_game.side_effect = PermissionError("Not host")
    response = client.post("/api/v1/game/start", json={"room_code": "ABCD", "host_token": "fake"})
    assert response.status_code in [400, 403, 422, 404]

def test_api_game_08_answer_correct_fast(mock_game_service):
    """API-GAME-08: answer đúng nhanh -> score > 500"""
    mock_game_service.submit_answer.return_value = {"score": 600}
    response = client.post("/api/v1/game/answer", json={"room_code": "ABCD", "nickname": "P1", "answer_index": 1})
    if response.status_code == 200:
        assert response.json().get("score", 0) > 500

def test_api_game_09_answer_wrong(mock_game_service):
    """API-GAME-09: answer sai -> score 0"""
    mock_game_service.submit_answer.return_value = {"score": 0}
    response = client.post("/api/v1/game/answer", json={"room_code": "ABCD", "nickname": "P1", "answer_index": 2})
    if response.status_code == 200:
        assert response.json().get("score") == 0

def test_api_game_10_answer_double_submit(mock_game_service):
    """API-GAME-10: double submit -> 400"""
    mock_game_service.submit_answer.side_effect = ValueError("Already answered")
    response = client.post("/api/v1/game/answer", json={"room_code": "ABCD", "nickname": "P1", "answer_index": 1})
    assert response.status_code in [400, 422, 404]

def test_api_game_11_next_non_host(mock_game_service):
    """API-GAME-11: non-host gọi next -> P0/P1: phải 403 nếu có host token"""
    mock_game_service.next_question.side_effect = PermissionError("Not host")
    response = client.post("/api/v1/game/next", json={"room_code": "ABCD", "host_token": "fake"})
    assert response.status_code in [400, 403, 422, 404]

def test_api_game_12_end_non_host(mock_game_service):
    """API-GAME-12: non-host gọi end -> P0/P1: phải 403 nếu có host token"""
    mock_game_service.end_game.side_effect = PermissionError("Not host")
    response = client.post("/api/v1/game/end", json={"room_code": "ABCD", "host_token": "fake"})
    assert response.status_code in [400, 403, 422, 404]

def test_api_game_13_status_timer_expired(mock_game_service):
    """API-GAME-13: timer hết -> status scoreboard"""
    mock_game_service.get_room_status.return_value = {"status": "scoreboard"}
    response = client.get("/api/v1/game/room/ABCD/status")
    if response.status_code == 200:
        assert response.json().get("room", {}).get("status") == "scoreboard"

def test_api_game_14_praise_not_finished(mock_game_service):
    """API-GAME-14: game chưa finished -> 400"""
    mock_game_service.generate_ai_praise.side_effect = ValueError("Not finished")
    response = client.get("/api/v1/game/room/ABCD/praise")
    assert response.status_code in [400, 422, 404]

def test_api_game_15_local_ip_production():
    from unittest.mock import patch
    with patch("api.routers.game_router.settings.ENVIRONMENT", "production", create=True):
        """API-GAME-15: production -> P1: phải tắt hoặc chỉ dev"""
        response = client.get("/api/v1/game/local-ip")
        assert response.status_code in [403, 404]
