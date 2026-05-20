from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app


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
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/v1/feedback",
        json={"message_id": "ai-1", "rating": "helpful"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_metrics_contract() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "counters" in data
    assert "durations" in data
