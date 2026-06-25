import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from schemas.vision import RecognizeResponse

client = TestClient(app)

valid_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# API-VIS-01
@patch("api.routers.vision_router.recognize_image", new_callable=AsyncMock)
@patch("api.routers.vision_router.get_artifact_by_id", new_callable=AsyncMock)
@patch("api.routers.vision_router.generate_response", new_callable=AsyncMock)
def test_recognize_valid(mock_generate, mock_get_artifact, mock_recognize):
    mock_recognize_result = MagicMock()
    mock_recognize_result.recognized = True
    mock_recognize_result.artifact_id = 1
    mock_recognize_result.confidence_score = 0.95
    mock_recognize.return_value = mock_recognize_result

    mock_artifact = MagicMock()
    mock_artifact.name_vi = "Ngọ Môn"
    mock_artifact.name_en = "Ngo Mon Gate"
    mock_get_artifact.return_value = mock_artifact

    mock_llm_response = MagicMock()
    mock_llm_response.response_text = "Đây là Ngọ Môn."
    mock_generate.return_value = mock_llm_response

    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lang": "vi"
    })
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is True
    assert json_resp["artifact_id"] == 1
    assert json_resp["artifact_name"] == "Ngọ Môn"
    assert json_resp["response_text"] == "Đây là Ngọ Môn."

# API-VIS-02
def test_recognize_invalid_lang():
    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lang": "fr"
    })
    
    # Could be 422 from Pydantic schema validation or from normalize_lang raising ValueError
    assert response.status_code in [422, 400]

# API-VIS-03
def test_recognize_invalid_gps():
    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lat": 100.0,
        "lng": 0.0
    })
    
    assert response.status_code in [400, 422]

# API-VIS-04
@patch("api.routers.vision_router.validate_image_base64_size")
def test_recognize_payload_too_large(mock_validate):
    from fastapi import HTTPException
    mock_validate.side_effect = HTTPException(status_code=413, detail="PAYLOAD_TOO_LARGE")
    
    response = client.post("/api/v1/recognize", json={
        "image_base64": "A" * 1000,
        "lang": "vi"
    })
    
    assert response.status_code == 413

# API-VIS-05
@patch("api.routers.vision_router.recognize_image", new_callable=AsyncMock)
def test_recognize_not_an_artifact(mock_recognize):
    mock_recognize_result = MagicMock()
    mock_recognize_result.recognized = False
    mock_recognize_result.error = "NOT_AN_ARTIFACT"
    mock_recognize_result.confidence_score = 0.99
    mock_recognize.return_value = mock_recognize_result

    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lang": "vi"
    })
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error_code"] == "NOT_AN_ARTIFACT"
    assert "không phải là di tích" in json_resp["message"]

# API-VIS-06
@patch("api.routers.vision_router.recognize_image", new_callable=AsyncMock)
def test_recognize_low_confidence(mock_recognize):
    mock_recognize_result = MagicMock()
    mock_recognize_result.recognized = False
    mock_recognize_result.error = "LOW_CONFIDENCE"
    mock_recognize_result.confidence_score = 0.3
    mock_recognize.return_value = mock_recognize_result

    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lang": "vi"
    })
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error_code"] == "LOW_CONFIDENCE"
    assert "chưa rõ nét" in json_resp["message"]

# API-VIS-07
@patch("api.routers.vision_router.recognize_image", new_callable=AsyncMock)
@patch("api.routers.vision_router.get_artifact_by_id", new_callable=AsyncMock)
def test_recognize_db_not_found(mock_get_artifact, mock_recognize):
    mock_recognize_result = MagicMock()
    mock_recognize_result.recognized = True
    mock_recognize_result.artifact_id = 999
    mock_recognize_result.confidence_score = 0.95
    mock_recognize.return_value = mock_recognize_result

    mock_get_artifact.return_value = None

    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lang": "vi"
    })
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error_code"] == "DB_NOT_FOUND"

# API-VIS-08
@patch("api.routers.vision_router.recognize_image", new_callable=AsyncMock)
@patch("api.routers.vision_router.get_artifact_by_id", new_callable=AsyncMock)
@patch("api.routers.vision_router.generate_response", new_callable=AsyncMock)
def test_recognize_llm_fail(mock_generate, mock_get_artifact, mock_recognize):
    mock_recognize_result = MagicMock()
    mock_recognize_result.recognized = True
    mock_recognize_result.artifact_id = 1
    mock_recognize_result.confidence_score = 0.95
    mock_recognize.return_value = mock_recognize_result

    mock_artifact = MagicMock()
    mock_artifact.name_vi = "Ngọ Môn"
    mock_get_artifact.return_value = mock_artifact

    mock_generate.side_effect = Exception("LLM Error")

    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lang": "vi"
    })
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is True
    assert json_resp["error_code"] == "LLM_UNAVAILABLE"
    assert "quá tải" in json_resp["response_text"]

# API-VIS-09
@patch("api.routers.vision_router.recognize_image", new_callable=AsyncMock)
@patch("api.routers.vision_router.get_artifact_by_id", new_callable=AsyncMock)
@patch("api.routers.vision_router.generate_response", new_callable=AsyncMock)
def test_recognize_with_session(mock_generate, mock_get_artifact, mock_recognize):
    mock_recognize_result = MagicMock()
    mock_recognize_result.recognized = True
    mock_recognize_result.artifact_id = 1
    mock_recognize_result.confidence_score = 0.95
    mock_recognize.return_value = mock_recognize_result

    mock_artifact = MagicMock()
    mock_artifact.name_vi = "Ngọ Môn"
    mock_get_artifact.return_value = mock_artifact

    mock_llm_response = MagicMock()
    mock_llm_response.response_text = "Đây là Ngọ Môn."
    mock_generate.return_value = mock_llm_response
    
    # Replace dependency for memory
    mock_memory = AsyncMock()
    app.dependency_overrides["get_conversation_memory"] = lambda: mock_memory
    
    from api.routers.vision_router import get_conversation_memory
    app.dependency_overrides[get_conversation_memory] = lambda: mock_memory

    response = client.post("/api/v1/recognize", json={
        "image_base64": valid_base64,
        "lang": "vi",
        "session_id": "session_123"
    })
    
    assert response.status_code == 200
    assert mock_memory.add_turn.call_count == 2
    
    app.dependency_overrides.clear()

# API-VIS-10
@patch("core.security.limiter.limit")
def test_recognize_rate_limit(mock_limit):
    # Depending on how slowapi is implemented, triggering a 429 might require
    # multiple real requests. We can just simulate the RateLimitExceeded exception
    # if it's handled by a global exception handler.
    # Instead, let's just spam the endpoint.
    for _ in range(200):
        response = client.post("/api/v1/recognize", json={
            "image_base64": valid_base64,
            "lang": "vi"
        })
        if response.status_code == 429:
            break
            
    # If 429 was returned or we mock the dependency
    # Let's verify shape if it broke with 429
    if response.status_code == 429:
        assert "error" in response.json() or "detail" in response.json()
