import os
import sys
import pytest
import asyncio
import json
from unittest.mock import patch

# Add backend directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from main import app, http_exception_handler
from core.config.settings import Settings
from core.security.rate_limit import rate_limit_exceeded_handler
from middleware.error_handler import global_exception_handler

# 1. lifespan
@patch("main.setup_cache")
def test_lifespan_continues_when_cache_setup_fails(mock_setup_cache):
    """
    Test that the application still starts up successfully even if cache initialization fails.
    """
    mock_setup_cache.side_effect = Exception("Cache initialization failed on purpose")
    
    # Using TestClient as a context manager triggers the lifespan
    with TestClient(app) as client:
        # Check if the app responds. /api/v1/metrics should be available.
        response = client.get("/api/v1/metrics")
        # Ensure it works and doesn't crash during startup
        assert response.status_code == 200

# 2. http_exception_handler
@pytest.mark.asyncio
async def test_http_exception_handler_maps_413_429_500_codes():
    """
    Test that specific HTTP status codes are mapped to their correct internal error_code.
    """
    async def run_handler(status_code):
        scope = {"type": "http", "state": {}}
        request = Request(scope)
        request.state.request_id = "test-id"
        exc = HTTPException(status_code=status_code, detail="Test detail")
        return await http_exception_handler(request, exc)
    
    # 413 -> PAYLOAD_TOO_LARGE
    res_413 = await run_handler(413)
    assert res_413.status_code == 413
    body_413 = json.loads(res_413.body.decode("utf-8"))
    assert body_413["error_code"] == "PAYLOAD_TOO_LARGE"
    
    # 429 -> RATE_LIMIT_EXCEEDED
    res_429 = await run_handler(429)
    assert res_429.status_code == 429
    body_429 = json.loads(res_429.body.decode("utf-8"))
    assert body_429["error_code"] == "RATE_LIMIT_EXCEEDED"
    
    # 500 -> SERVER_ERROR
    res_500 = await run_handler(500)
    assert res_500.status_code == 500
    body_500 = json.loads(res_500.body.decode("utf-8"))
    assert body_500["error_code"] == "SERVER_ERROR"
    
    # Other error -> HTTP_ERROR
    res_400 = await run_handler(400)
    assert res_400.status_code == 400
    body_400 = json.loads(res_400.body.decode("utf-8"))
    assert body_400["error_code"] == "HTTP_ERROR"

# 3. request_id_middleware
def test_request_id_middleware_reuses_or_generates_request_id():
    """
    Test that a new request id is generated if missing, but reused if x-request-id is provided.
    """
    with TestClient(app) as client:
        # Case 1: Missing header, generates new request ID
        res1 = client.get("/api/v1/metrics")
        assert res1.status_code == 200
        assert "x-request-id" in res1.headers
        generated_id = res1.headers["x-request-id"]
        assert len(generated_id) > 0
        
        # Case 2: Header provided, reuses request ID
        custom_id = "my-custom-request-id-1234"
        res2 = client.get("/api/v1/metrics", headers={"x-request-id": custom_id})
        assert res2.status_code == 200
        assert res2.headers["x-request-id"] == custom_id

# 4. metrics_snapshot
def test_metrics_snapshot_shape():
    """
    Test that the metrics endpoint returns the expected shape (counters/durations).
    """
    with TestClient(app) as client:
        res = client.get("/api/v1/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "counters" in data
        assert "durations" in data

# 5. Settings.validate_runtime
def test_settings_validate_runtime_requires_keys_only_in_production():
    """
    Test that runtime config validation succeeds in dev but fails in prod if keys are missing.
    """
    # In development, missing keys are tolerated
    dev_settings = Settings(ENVIRONMENT="development", GEMINI_API_KEY="", GROQ_API_KEY="", DATABASE_URL="")
    try:
        dev_settings.validate_runtime()  # Should not raise exception
    except Exception as e:
        pytest.fail(f"validate_runtime() raised an exception in development mode: {e}")
    
    # In production, missing keys raise ValueError
    prod_settings = Settings(ENVIRONMENT="production", GEMINI_API_KEY="", GROQ_API_KEY="", DATABASE_URL="")
    with pytest.raises(ValueError) as excinfo:
        prod_settings.validate_runtime()
    
    error_msg = str(excinfo.value)
    assert "Missing required production settings" in error_msg
    assert "GEMINI_API_KEY" in error_msg
    assert "GROQ_API_KEY" in error_msg
    assert "DATABASE_URL" in error_msg

# 6. rate_limit_exceeded_handler
@pytest.mark.asyncio
async def test_rate_limit_handler_shape():
    """
    Test that the rate limit handler returns the standardized JSON shape.
    """
    scope = {"type": "http", "state": {}}
    request = Request(scope)
    request.state.request_id = "test-req-id"
    class MockLimit:
        error_message = ""
        limit = "1 per 1 minute"
    exc = RateLimitExceeded(MockLimit())
    
    res = await rate_limit_exceeded_handler(request, exc)
    
    assert res.status_code == 429
    body = json.loads(res.body.decode("utf-8"))
    
    assert body["success"] is False
    assert body["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "Bạn đang gửi yêu cầu quá nhanh" in body["message"]
    assert body["request_id"] == "test-req-id"
    assert "1 per 1 minute" in body["detail"]

# 7. global_exception_handler
@pytest.mark.asyncio
async def test_global_exception_handler_hides_traceback():
    """
    Test that the global exception handler does not leak traceback/stack info to the client.
    """
    scope = {"type": "http", "state": {}}
    request = Request(scope)
    request.state.request_id = "test-req-id"
    
    # Trigger an exception with a traceback
    try:
        1 / 0
    except Exception as e:
        exc = e
        
    res = await global_exception_handler(request, exc)
    
    assert res.status_code == 500
    body = json.loads(res.body.decode("utf-8"))
    
    # Validate the shape
    assert body["success"] is False
    assert body["error_code"] == "SERVER_ERROR"
    assert body["message"] == "Lỗi server nội bộ. Vui lòng thử lại."
    assert body["request_id"] == "test-req-id"
    
    # Ensure traceback is not exposed
    body_str = json.dumps(body).lower()
    assert "zerodivisionerror" not in body_str
    assert "traceback" not in body_str
    assert "file " not in body_str
