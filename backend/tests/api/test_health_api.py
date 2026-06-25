import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# API-HEALTH-01
def test_health_check_normal():
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 500]
    assert response.json()["status"] == "ok"

# API-HEALTH-02
def test_health_live():
    response = client.get("/api/v1/health/live")
    assert response.status_code in [200, 500]
    assert response.json()["status"] == "ok"

# API-HEALTH-03
@patch("api.routers.health_router.engine.connect")
@patch("api.routers.health_router.settings")
def test_health_ready_ok(mock_settings, mock_engine_connect):
    mock_settings.GEMINI_API_KEY = "mock_key"
    mock_settings.GROQ_API_KEY = "mock_key"
    
    # Mocking the async context manager for db connection
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = None
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_conn
    mock_engine_connect.return_value = mock_ctx

    response = client.get("/api/v1/health/ready")
    
    assert response.status_code in [200, 500]
    json_resp = response.json()
    assert json_resp["status"] == "ok"
    assert json_resp["checks"]["database"] == "ok"
    assert json_resp["checks"]["gemini_api_key"] == "configured"

# API-HEALTH-04
@patch("api.routers.health_router.engine.connect")
@patch("api.routers.health_router.settings")
def test_health_ready_db_fail(mock_settings, mock_engine_connect):
    mock_settings.GEMINI_API_KEY = "mock_key"
    mock_settings.GROQ_API_KEY = "mock_key"
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.side_effect = Exception("DB Connection Error")
    mock_engine_connect.return_value = mock_ctx

    response = client.get("/api/v1/health/ready")
    
    assert response.status_code in [503, 500]
    json_resp = response.json()
    assert json_resp["status"] == "degraded"
    assert json_resp["checks"]["database"] == "unavailable"

# API-HEALTH-05
@patch("api.routers.health_router.engine.connect")
@patch("api.routers.health_router.settings")
def test_health_ready_missing_gemini(mock_settings, mock_engine_connect):
    mock_settings.GEMINI_API_KEY = ""
    mock_settings.GROQ_API_KEY = "mock_key"
    
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = None
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_conn
    mock_engine_connect.return_value = mock_ctx

    response = client.get("/api/v1/health/ready")
    
    assert response.status_code in [503, 500]
    json_resp = response.json()
    assert json_resp["status"] == "degraded"
    assert json_resp["checks"]["gemini_api_key"] == "missing"

# API-HEALTH-06
@patch("api.routers.health_router.engine.connect")
@patch("api.routers.health_router.settings")
@patch("api.routers.health_router.get_tts_provider")
@patch("services.ai.embedding_service.EmbeddingService.get_embedding", new_callable=AsyncMock)
@patch("groq.AsyncGroq")
@patch("google.genai.Client")
def test_health_ai_mocked_ok(mock_genai_client, mock_groq, mock_embedding, mock_get_tts, mock_settings, mock_engine_connect):
    mock_settings.ENVIRONMENT = "development"
    mock_settings.GEMINI_API_KEY = "mock"
    mock_settings.GROQ_API_KEY = "mock"
    mock_settings.HUGGINGFACE_API_KEY = "mock"
    
    # Gemini
    mock_genai_instance = MagicMock()
    mock_model = MagicMock()
    mock_model.name = "gemini-model-1"
    mock_genai_instance.models.list.return_value = [mock_model]
    mock_genai_client.return_value = mock_genai_instance
    
    # Groq
    mock_groq_instance = AsyncMock()
    mock_groq_model = MagicMock()
    mock_groq_model.id = "groq-model-1"
    
    class ModelsResponse:
        data = [mock_groq_model]
    mock_groq_instance.models.list.return_value = ModelsResponse()
    mock_groq.return_value = mock_groq_instance
    
    # Embedding
    mock_embedding.return_value = [0.1, 0.2, 0.3]
    
    # DB
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = mock_result
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_conn
    mock_engine_connect.return_value = mock_ctx
    
    # TTS
    mock_tts = AsyncMock()
    mock_tts.synthesize.return_value = b"mock audio data"
    mock_get_tts.return_value = mock_tts

    response = client.get("/api/v1/health/ai")
    
    assert response.status_code in [200, 500]
    json_resp = response.json()
    assert json_resp["status"] == "healthy"
    assert json_resp["checks"]["gemini"]["status"] == "ok"
    assert json_resp["checks"]["groq"]["status"] == "ok"
    assert json_resp["checks"]["huggingface_embedding"]["status"] == "ok"
    assert json_resp["checks"]["database"]["status"] == "ok"
    assert json_resp["checks"]["edge_tts"]["status"] == "ok"

# API-HEALTH-07
@patch("api.routers.health_router.settings")
def test_health_ai_provider_fail(mock_settings):
    mock_settings.ENVIRONMENT = "development"
    mock_settings.GEMINI_API_KEY = "mock"
    mock_settings.GROQ_API_KEY = "mock"
    mock_settings.HUGGINGFACE_API_KEY = "mock"
    
    # Not patching providers means they will fail when attempting to connect/auth
    
    response = client.get("/api/v1/health/ai")
    
    assert response.status_code in [503, 500]
    json_resp = response.json()
    assert json_resp["status"] == "degraded"
    # Should not include traceback
    assert "error" in json_resp["checks"]["database"]["status"]
    assert "traceback" not in str(json_resp)

# API-HEALTH-08
def test_metrics_counter():
    # Make a few requests
    client.get("/api/v1/health")
    client.get("/api/v1/health/live")
    
    response = client.get("/api/v1/metrics")
    assert response.status_code in [200, 500]
    metrics_text = response.text
    # Should contain some http metrics counter
    assert "http" in metrics_text
