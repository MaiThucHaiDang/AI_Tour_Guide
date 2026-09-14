import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import hashlib

from schemas.vision import ArtifactInfo, LLMResponse
from backend.services.vision import response_generator
from backend.services.vision.response_generator import (
    _get_text_client,
    _make_cache_key,
    _manage_cache_size,
    generate_response,
    _response_cache,
    _MAX_CACHE_SIZE,
)

@pytest.fixture
def dummy_artifact():
    return ArtifactInfo(
        art_id="test_art_001",
        loc_id="loc_1",
        name_vi="Test Artifact",
        name_en="Test Artifact",
        history_text_vi="A test artifact",
        history_text_en="A test artifact"
    )

@pytest.fixture(autouse=True)
def reset_cache():
    # Reset internal states before each test
    response_generator._response_cache.clear()
    response_generator._text_client = None
    yield

@patch("backend.services.vision.response_generator.settings")
def test_get_text_client_requires_gemini_key(mock_settings):
    """thiếu key raise RuntimeError"""
    mock_settings.GEMINI_API_KEY = ""
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        _get_text_client()

def test_make_cache_key_changes_by_artifact_lang_question():
    """key khác nhau"""
    key1 = _make_cache_key("art_1", "vi", "question A")
    key2 = _make_cache_key("art_1", "vi", "question B")
    key3 = _make_cache_key("art_1", "en", "question A")
    key4 = _make_cache_key("art_2", "vi", "question A")
    assert key1 != key2
    assert key1 != key3
    assert key1 != key4
    
def test_manage_cache_size_evicts_oldest_twenty_percent():
    """cache <= max"""
    # Fill cache beyond max
    for i in range(_MAX_CACHE_SIZE + 10):
        _response_cache[f"key_{i}"] = LLMResponse(response_text=f"val_{i}", token_count=0, model_used="")
    
    _manage_cache_size()
    
    # Should evict oldest 20%
    expected_remaining = (_MAX_CACHE_SIZE + 10) - ((_MAX_CACHE_SIZE + 10) // 5)
    assert len(_response_cache) == expected_remaining
    # The oldest keys (key_0, key_1, ...) should be removed
    assert "key_0" not in _response_cache

@pytest.mark.asyncio
@patch("backend.services.vision.response_generator._get_text_client")
@patch("backend.services.vision.response_generator.settings")
async def test_generate_response_returns_cached_result(mock_settings, mock_get_client, dummy_artifact):
    """không gọi Gemini lần 2"""
    mock_settings.GEMINI_TEXT_MODEL = "test-model"
    # Pre-fill cache
    cache_key = _make_cache_key(dummy_artifact.art_id, "vi", "question")
    cached_resp = LLMResponse(response_text="cached response", token_count=0, model_used="")
    _response_cache[cache_key] = cached_resp
    
    result = await generate_response(dummy_artifact, "vi", "question")
    assert result == cached_resp
    mock_get_client.assert_not_called()

@pytest.mark.asyncio
@patch("backend.services.vision.response_generator._get_text_client")
@patch("backend.services.vision.response_generator.settings")
async def test_generate_response_retries_empty_response(mock_settings, mock_get_client, dummy_artifact):
    """retry trước khi fail"""
    mock_settings.GEMINI_TEXT_MODEL = "test-model"
    
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_resp_empty = MagicMock()
    mock_resp_empty.text = "   "  # will be stripped to empty
    
    mock_resp_success = MagicMock()
    mock_resp_success.text = "success text"
    
    mock_client.aio.models.generate_content = AsyncMock(side_effect=[mock_resp_empty, mock_resp_success])
    
    # Mock sleep to run fast
    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        result = await generate_response(dummy_artifact, "vi", "question")
        
    assert result.response_text == "success text"
    assert mock_client.aio.models.generate_content.call_count == 2
    mock_sleep.assert_called_once()

@pytest.mark.asyncio
@patch("backend.services.vision.response_generator._get_text_client")
@patch("backend.services.vision.response_generator.settings")
async def test_generate_response_retries_429_timeout_then_success(mock_settings, mock_get_client, dummy_artifact):
    """success sau retry"""
    mock_settings.GEMINI_TEXT_MODEL = "test-model"
    
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_resp_success = MagicMock()
    mock_resp_success.text = "success text"
    
    # raise Exception("429 Too Many Requests") for first attempt, then success
    mock_client.aio.models.generate_content = AsyncMock(side_effect=[Exception("429 Too Many Requests"), mock_resp_success])
    
    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        result = await generate_response(dummy_artifact, "vi", "question")
        
    assert result.response_text == "success text"
    assert mock_client.aio.models.generate_content.call_count == 2
    mock_sleep.assert_called_once()

@pytest.mark.asyncio
@patch("backend.services.vision.response_generator._get_text_client")
@patch("backend.services.vision.response_generator.settings")
async def test_generate_response_raises_non_retryable_error(mock_settings, mock_get_client, dummy_artifact):
    """raise ngay hoặc sau logic hiện tại"""
    mock_settings.GEMINI_TEXT_MODEL = "test-model"
    
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # raise some non-retryable error (e.g. ValueError)
    mock_client.aio.models.generate_content = AsyncMock(side_effect=ValueError("Invalid request"))
    
    with pytest.raises(ValueError, match="Invalid request"):
        await generate_response(dummy_artifact, "vi", "question")
    
    # Should only call once for non-retryable errors
    assert mock_client.aio.models.generate_content.call_count == 1

@pytest.mark.asyncio
@patch("backend.services.vision.response_generator._get_text_client")
@patch("backend.services.vision.response_generator.settings")
async def test_generate_response_uses_configured_model_name(mock_settings, mock_get_client, dummy_artifact):
    """model đúng settings"""
    mock_settings.GEMINI_TEXT_MODEL = "test-custom-model"
    
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_resp_success = MagicMock()
    mock_resp_success.text = "success text"
    
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp_success)
    
    result = await generate_response(dummy_artifact, "vi", "question")
    
    assert result.model_used == "test-custom-model"
    mock_client.aio.models.generate_content.assert_called_once()
    args, kwargs = mock_client.aio.models.generate_content.call_args
    assert kwargs["model"] == "test-custom-model"
