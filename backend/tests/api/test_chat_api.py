from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app
from orchestrators.unified_orchestrator import MIN_AUDIO_BYTES
from core.config import settings

client = TestClient(app, raise_server_exceptions=False)

def _mock_unified_result(**kwargs):
    result = MagicMock()
    result.response_text = kwargs.get("response_text", "Success")
    result.speech_text = kwargs.get("speech_text", "Success")
    result.audio_bytes = kwargs.get("audio_bytes", None)
    result.transcript = kwargs.get("transcript", None)
    result.artifact_id = kwargs.get("artifact_id", None)
    result.artifact_name = kwargs.get("artifact_name", None)
    result.detected_lang = kwargs.get("detected_lang", "vi")
    result.answer_source = kwargs.get("answer_source", "llm")
    result.processing_steps = kwargs.get("processing_steps", [])
    result.artifact_year = kwargs.get("artifact_year", None)
    result.artifact_author = kwargs.get("artifact_author", None)
    result.artifact_summary = kwargs.get("artifact_summary", None)
    result.tts_token = kwargs.get("tts_token", None)
    return result


@patch("orchestrators.unified_orchestrator.UnifiedOrchestrator.process_chat_request")
@patch("api.routers.chat_router.get_stt_provider")
def test_chat_01_text_greeting(mock_get_stt, mock_process):
    # API-CHAT-01: text greeting
    mock_process.return_value = _mock_unified_result(answer_source="template")
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "chào bạn", "lang": "vi"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer_source"] == "template"
    assert not data.get("audio_base64")


@patch("orchestrators.unified_orchestrator.UnifiedOrchestrator.process_chat_request")
@patch("api.routers.chat_router.get_stt_provider")
def test_chat_02_text_artifact(mock_get_stt, mock_process):
    # API-CHAT-02: text về artifact
    mock_process.return_value = _mock_unified_result(
        artifact_id=1,
        artifact_name="Ngọ Môn",
        artifact_year=1833,
        artifact_author="Minh Mạng",
        artifact_summary="Cửa chính của Hoàng thành Huế"
    )
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "kể về ngọ môn", "lang": "vi"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["artifact_id"] == "1"
    assert data["artifact_name"] == "Ngọ Môn"
    assert data["artifact_year"] == 1833
    assert data["artifact_author"] == "Minh Mạng"
    assert data["artifact_summary"] == "Cửa chính của Hoàng thành Huế"


def test_chat_03_text_too_long():
    # API-CHAT-03: text > TEXT_MAX_CHARS -> 413
    long_text = "a" * (settings.TEXT_MAX_CHARS + 1)
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": long_text, "lang": "vi"}
    )
    assert response.status_code == 413


def test_chat_04_session_id_too_long():
    # API-CHAT-04: session_id > 255 -> 400
    long_session = "a" * 256
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "hello", "lang": "vi", "session_id": long_session}
    )
    assert response.status_code == 400


def test_chat_05_lat_lng_out_of_range():
    # API-CHAT-05: lat/lng out of range -> 400
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "hello", "lang": "vi", "lat": 100, "lng": 200}
    )
    assert response.status_code == 400


def test_chat_06_artifact_id_invalid():
    # API-CHAT-06: artifact_id <= 0 -> 400
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "hello", "lang": "vi", "artifact_id": 0}
    )
    assert response.status_code == 400


@patch("orchestrators.unified_orchestrator.UnifiedOrchestrator.process_chat_request")
@patch("api.routers.chat_router.get_stt_provider")
def test_chat_07_tiny_audio(mock_get_stt, mock_process):
    # API-CHAT-07: tiny audio -> 200, message chưa nghe rõ, không init STT
    mock_process.return_value = _mock_unified_result(response_text="Xin lỗi, tôi chưa nghe rõ", answer_source="template")
    
    tiny_audio = b"123" # length 3 < MIN_AUDIO_BYTES
    response = client.post(
        "/api/v1/chat/unified",
        data={"lang": "vi"},
        files={"audio": ("test.mp3", tiny_audio, "audio/mpeg")}
    )
    assert response.status_code == 200
    mock_get_stt.assert_not_called()
    assert response.json()["response_text"] == "Xin lỗi, tôi chưa nghe rõ"


def test_chat_08_audio_too_large():
    # API-CHAT-08: audio lớn hơn limit -> 413
    # MAX_AUDIO_MB = 10 -> >10MB
    large_audio = b"0" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/chat/unified",
        data={"lang": "vi"},
        files={"audio": ("large.mp3", large_audio, "audio/mpeg")}
    )
    assert response.status_code == 413


@patch("api.routers.chat_router.get_stt_provider")
def test_chat_09_audio_no_stt_provider(mock_get_stt):
    # API-CHAT-09: audio đủ lớn nhưng thiếu STT provider -> 503
    mock_get_stt.side_effect = Exception("No STT")
    valid_audio = b"0" * MIN_AUDIO_BYTES
    response = client.post(
        "/api/v1/chat/unified",
        data={"lang": "vi"},
        files={"audio": ("test.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 503


@patch("orchestrators.unified_orchestrator.UnifiedOrchestrator.process_chat_request")
@patch("api.routers.chat_router.get_stt_provider")
def test_chat_10_image_and_text(mock_get_stt, mock_process):
    # API-CHAT-10: image + text -> câu trả lời bám chi tiết ảnh trước
    mock_process.return_value = _mock_unified_result(response_text="Tôi thấy mái ngói trong ảnh", answer_source="vision")
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "đây là gì", "image_base64": "data:image/jpeg;base64,123", "lang": "vi"}
    )
    assert response.status_code == 200
    assert response.json()["answer_source"] == "vision"


@patch("orchestrators.unified_orchestrator.UnifiedOrchestrator.process_chat_request")
@patch("api.routers.chat_router.get_stt_provider")
def test_chat_11_image_fail_artifact_fallback(mock_get_stt, mock_process):
    # API-CHAT-11: image fail + artifact_id có sẵn -> vẫn trả lời theo artifact context
    mock_process.return_value = _mock_unified_result(
        response_text="Ngọ Môn là...",
        artifact_id=1,
        answer_source="llm"
    )
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "đây là gì", "image_base64": "data:image/jpeg;base64,fail", "lang": "vi", "artifact_id": 1}
    )
    assert response.status_code == 200
    assert response.json()["artifact_id"] == "1"


@patch("orchestrators.unified_orchestrator.UnifiedOrchestrator.process_chat_request")
@patch("api.routers.chat_router.get_stt_provider")
def test_chat_12_llm_fail(mock_get_stt, mock_process):
    # API-CHAT-12: LLM fail -> response fallback, không 500
    mock_process.return_value = _mock_unified_result(
        response_text="Xin lỗi, hiện tại tôi đang gặp chút sự cố",
        answer_source="fallback"
    )
    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "hello", "lang": "vi"}
    )
    assert response.status_code == 200
    assert response.json()["answer_source"] == "fallback"


def test_chat_13_tts_fetch_invalid_token():
    # API-CHAT-13: GET /api/v1/tts/fetch token rỗng/quá dài -> 400
    response1 = client.get("/api/v1/tts/fetch?tts_token=")
    assert response1.status_code == 400
    
    long_token = "a" * 65
    response2 = client.get(f"/api/v1/tts/fetch?tts_token={long_token}")
    assert response2.status_code == 400


@patch("api.routers.chat_router.UnifiedOrchestrator.fetch_tts_status")
def test_chat_14_tts_fetch_pending(mock_fetch):
    # API-CHAT-14: GET /api/v1/tts/fetch token pending -> {status: pending}
    mock_fetch.return_value = {"status": "pending"}
    response = client.get("/api/v1/tts/fetch?tts_token=123")
    assert response.status_code == 200
    assert response.json() == {"status": "pending"}


@patch("api.routers.chat_router.UnifiedOrchestrator.fetch_tts_status")
def test_chat_15_tts_fetch_ready(mock_fetch):
    # API-CHAT-15: GET /api/v1/tts/fetch token ready -> audio_base64, mime
    mock_fetch.return_value = {"status": "ready", "audio_bytes": b"test"}
    response = client.get("/api/v1/tts/fetch?tts_token=123")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "audio_base64" in data
    assert data["audio_mime"] == "audio/mpeg"


@patch("api.routers.chat_router.UnifiedOrchestrator.fetch_tts_status")
def test_chat_16_tts_fetch_failed(mock_fetch):
    # API-CHAT-16: GET /api/v1/tts/fetch token failed/expired -> status và message rõ
    mock_fetch.return_value = {"status": "failed", "error": "Internal Error"}
    response = client.get("/api/v1/tts/fetch?tts_token=123")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["message"] == "Internal Error"
