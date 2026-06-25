from __future__ import annotations
from core.database import get_db_session

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app

def test_feedback_helpful_success() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("api.routers.feedback_router.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_db.return_value = mock_session
        
        response = client.post(
            "/api/v1/feedback",
            json={
                "rating": "helpful",
                "session_id": "session_123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

def test_feedback_not_helpful_with_comment() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("api.routers.feedback_router.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_db.return_value = mock_session
        
        response = client.post(
            "/api/v1/feedback",
            json={
                "rating": "not_helpful",
                "comment": "This did not answer my question about Ngọ Môn."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

def test_feedback_invalid_rating() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/feedback",
        json={
            "rating": "5_stars",
            "comment": "Awesome!"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert any(err["loc"][-1] == "rating" for err in data["detail"])

def test_feedback_comment_too_long() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/feedback",
        json={
            "rating": "not_helpful",
            "comment": "A" * 501
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert any(err["loc"][-1] == "comment" for err in data["detail"])

def test_feedback_db_commit_failure_returns_503() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    # Fastapi depends override
    with patch("api.routers.feedback_router.get_db_session") as mock_db_dep:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush.side_effect = Exception("DB Connection Lost")
        mock_session.commit.side_effect = Exception("DB Connection Lost")
        mock_db_dep.return_value = mock_session
        
        # Override the Depends
        app.dependency_overrides[get_db_session] = lambda: mock_session
        patcher = patch('core.database.async_session_factory')
        mock_factory = patcher.start()
        mock_factory.return_value.__aenter__.return_value = mock_session
        import atexit
        atexit.register(patcher.stop)
        
        response = client.post(
            "/api/v1/feedback",
            json={
                "rating": "helpful"
            }
        )
        # Ensure fallback
        app.dependency_overrides.clear()
        
    if response.status_code != 503:
        print("ERROR RESPONSE:", response.json())
    assert response.status_code == 503
    assert response.json()["detail"] == "Unable to record feedback right now."

def test_feedback_rate_limit() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("api.routers.feedback_router.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_db.return_value = mock_session
        
        # Simulate rate limit by patching the limiter
        with patch("core.security.limiter.limit") as mock_limit:
            # We must raise the error that slowapi normally raises
            from slowapi.errors import RateLimitExceeded
            
            def side_effect(*args, **kwargs):
                raise RateLimitExceeded("100 per 1 minute")
                
            mock_limit.side_effect = side_effect
            
            response = client.post(
                "/api/v1/feedback",
                json={
                    "rating": "helpful"
                }
            )
            
            # Note: because mock_limit replaces a decorator before the app starts, 
            # we can't easily patch it mid-flight for a FastAPI route since decorators 
            # are evaluated at import time. Instead, let's just make the actual 
            # limiter object always fail.
            pass

    # A better way to test rate limit in FastAPI with slowapi is to patch the Limiter's check method.
    with patch("slowapi.Limiter._check_request_limit") as mock_check:
        mock_check.side_effect = Exception("Rate Limit Exceeded")
        # FastAPI might not catch raw Exceptions into 429 if the handler expects RateLimitExceeded
        from fastapi import HTTPException
        mock_check.side_effect = HTTPException(status_code=429, detail="Rate Limit Exceeded")
        
        response = client.post(
            "/api/v1/feedback",
            json={
                "rating": "helpful"
            }
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"

