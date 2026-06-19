from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.database import get_db_session
from main import app
from schemas.vision import ArtifactInfo, VisionResult


def test_unified_chat_text_greeting_contract() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/v1/chat/unified",
        data={"text": "Chao ban", "lang": "vi", "session_id": "contract-test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["response_text"]
    assert data["answer_source"] == "template"
    assert data["audio_base64"] is None


def test_feedback_contract() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.added = None
            self.committed = False
            self.rolled_back = False

        def add(self, event) -> None:
            self.added = event

        async def flush(self) -> None:
            self.added.feedback_id = 42

        async def commit(self) -> None:
            self.committed = True

        async def rollback(self) -> None:
            self.rolled_back = True

    fake_session = FakeSession()

    async def override_db_session():
        yield fake_session

    app.dependency_overrides[get_db_session] = override_db_session
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.post(
            "/api/v1/feedback",
            json={
                "session_id": "session-1",
                "message_id": "ai-1",
                "artifact_id": "2",
                "rating": "helpful",
                "answer_source": "db_direct",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db_session, None)

    assert response.status_code == 200
    assert response.json() == {"success": True, "feedback_id": 42}
    assert fake_session.added is not None
    assert fake_session.added.session_id == "session-1"
    assert fake_session.added.message_id == "ai-1"
    assert fake_session.added.artifact_id == "2"
    assert fake_session.added.rating == "helpful"
    assert fake_session.added.answer_source == "db_direct"
    assert fake_session.committed is True
    assert fake_session.rolled_back is False


def test_metrics_contract() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "counters" in data
    assert "durations" in data


def test_unified_chat_tiny_audio_does_not_require_voice_provider() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    with patch("api.routers.chat_router.get_stt_provider", side_effect=AssertionError("STT should not initialize")), \
         patch("api.routers.chat_router.get_tts_provider", side_effect=AssertionError("TTS should not initialize")):
        response = client.post(
            "/api/v1/chat/unified",
            data={"lang": "vi", "session_id": "tiny-audio-test"},
            files={"audio": ("tiny.webm", b"x" * 20, "audio/webm")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "chưa nghe rõ" in data["response_text"].lower()
    assert data["audio_base64"] is None


def test_recognize_returns_artifact_when_llm_generation_fails() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    artifact = ArtifactInfo(
        art_id="16",
        name_vi="Điện Long An",
        name_en="Long An Palace",
        history_text_vi="Dữ liệu thử nghiệm",
        history_text_en="Test data",
        loc_id="loc-16",
    )
    vision = VisionResult(
        recognized=True,
        artifact_id="16",
        raw_label="Điện Long An",
        confidence_score=0.8,
    )

    with patch("api.routers.vision_router.recognize_image", AsyncMock(return_value=vision)), \
         patch("api.routers.vision_router.get_artifact_by_id", AsyncMock(return_value=artifact)), \
         patch("api.routers.vision_router.generate_response", AsyncMock(side_effect=RuntimeError("503 UNAVAILABLE"))):
        response = client.post(
            "/api/v1/recognize",
            json={"image_base64": "abcd", "lang": "vi", "session_id": "vision-fallback"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["artifact_id"] == "16"
    assert data["artifact_name"] == "Điện Long An"
    assert data["confidence_score"] == 0.8
    assert data["error_code"] == "LLM_UNAVAILABLE"
    assert "Đã nhận diện ảnh" in data["response_text"]
