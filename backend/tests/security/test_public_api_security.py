from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app

def test_chat_unified_rate_limit_exceeded() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("slowapi.Limiter._check_request_limit") as mock_check:
        from fastapi import HTTPException
        mock_check.side_effect = HTTPException(status_code=429, detail="Rate Limit Exceeded")
        
        response = client.post(
            "/api/v1/chat/unified",
            data={
                "message": "Hello",
                "session_id": "test_session"
            }
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"

def test_recognize_vision_payload_too_large() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    # The actual implementation might use FastAPI's max request size or explicitly check file size
    # We simulate a large base64 payload
    large_base64 = "A" * (6 * 1024 * 1024)  # 6MB base64 string
    
    response = client.post(
        "/api/v1/recognize",
        json={
            "image": f"data:image/jpeg;base64,{large_base64}",
            "lat": 16.467,
            "lng": 107.578
        }
    )
    # Expecting 413 Payload Too Large
    # Some setups return 422 if it's Pydantic validation
    assert response.status_code in (413, 422)

def test_voice_chat_audio_too_large() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    large_audio_content = b"0" * (9 * 1024 * 1024)  # 9MB dummy audio
    
    response = client.post(
        "/api/v1/voice/chat",
        data={
            "session_id": "test_session",
            "language": "vi"
        },
        files={"audio": ("large.webm", large_audio_content, "audio/webm")}
    )
    assert response.status_code in (413, 422)

def test_health_ai_rate_limit_exceeded() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("slowapi.Limiter._check_request_limit") as mock_check:
        from fastapi import HTTPException
        mock_check.side_effect = HTTPException(status_code=429, detail="Rate Limit Exceeded")
        
        response = client.get("/api/v1/health/ai")
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"

def test_blog_post_xss_rejection() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/blog-posts",
        json={
            "title": "Normal title",
            "content": "<script>alert(1)</script>",
            "author": "Test Author"
        }
    )
    # Assuming backend rejects HTML/XSS on create via Pydantic or custom validator
    assert response.status_code == 422

def test_blog_comment_xss_rejection() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/blog-posts/1/comments",
        json={
            "content": "<img src=x onerror=alert(1)>",
            "author": "Test Author"
        }
    )
    assert response.status_code == 422
