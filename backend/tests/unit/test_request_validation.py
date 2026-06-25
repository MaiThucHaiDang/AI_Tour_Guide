import pytest
import base64
from unittest.mock import patch
from fastapi import HTTPException
from utils.request_validation import (
    normalize_lang,
    validate_text_size,
    validate_image_base64_size,
    validate_audio_size,
    decode_image_base64,
    _strip_data_url,
    _estimate_base64_bytes,
)

@pytest.fixture
def mock_settings():
    with patch("utils.request_validation.settings") as mock_set:
        mock_set.TEXT_MAX_CHARS = 100
        mock_set.IMAGE_MAX_BYTES = 500
        mock_set.AUDIO_MAX_BYTES = 1000
        yield mock_set

@pytest.mark.parametrize("input_lang, expected", [
    ("vi", "vi"),
    ("en", "en"),
    ("VI", "vi"),
    ("EN", "en"),
    (" vi ", "vi"),
])
def test_normalize_lang_accepts_vi_en(input_lang, expected):
    """Test normal valid inputs for normalize_lang."""
    assert normalize_lang(input_lang) == expected

@pytest.mark.parametrize("invalid_lang", [
    "fr",
    "de",
    "vi-VN",
    "en-US",
    "",
    "   ",
    None,
    "123",
])
def test_normalize_lang_defaults_invalid_to_vi(invalid_lang):
    """Test that any invalid or unsupported language defaults to 'vi'."""
    assert normalize_lang(invalid_lang) == "vi"

@pytest.mark.parametrize("text", [
    None,
    "",
    "a",
    "a" * 100,  # Exact limit from mock
])
def test_validate_text_size_allows_empty_and_limit(text, mock_settings):
    """Test that text within the limits is accepted without raising exceptions."""
    validate_text_size(text)  # Should not raise

def test_validate_text_size_rejects_over_limit(mock_settings):
    """Test that text exceeding the limit raises HTTP 413."""
    over_limit_text = "a" * 101
    with pytest.raises(HTTPException) as exc:
        validate_text_size(over_limit_text)
    
    assert exc.value.status_code == 413
    assert "Nội dung quá dài" in str(exc.value.detail)

@pytest.mark.parametrize("payload", [
    None,
    "data:image/jpeg;base64,aGVsbG8=",
    "A" * 666, # Estimated size ~ 500 bytes (limit)
])
def test_validate_image_base64_size_accepts_data_url_under_limit(payload, mock_settings):
    """Test that base64 images within the size limit are accepted."""
    validate_image_base64_size(payload)  # Should not raise

@patch("utils.request_validation._estimate_base64_bytes")
def test_validate_image_base64_size_rejects_estimated_large_base64(mock_estimate, mock_settings):
    """Test that an image with estimated size over limit raises HTTP 413."""
    mock_estimate.return_value = 501  # Limit is 500
    
    with pytest.raises(HTTPException) as exc:
        validate_image_base64_size("dummy_base64_string")
    
    assert exc.value.status_code == 413
    assert "Ảnh quá lớn" in str(exc.value.detail)
    mock_estimate.assert_called_once_with("dummy_base64_string")

@pytest.mark.parametrize("audio_bytes", [
    None,
    b"",
    b"a" * 1000, # Exact limit
])
def test_validate_audio_size_accepts_under_limit(audio_bytes, mock_settings):
    """Test that audio within the size limit is accepted."""
    validate_audio_size(audio_bytes)  # Should not raise

def test_validate_audio_size_rejects_large_audio(mock_settings):
    """Test that audio exceeding the size limit raises HTTP 413."""
    large_audio = b"a" * 1001
    
    with pytest.raises(HTTPException) as exc:
        validate_audio_size(large_audio)
    
    assert exc.value.status_code == 413
    assert "Audio quá lớn" in str(exc.value.detail)

@pytest.mark.parametrize("prefix", [
    "data:image/png;base64,",
    "data:image/jpeg;base64,",
    "data:image/webp;base64,",
    "", # No prefix
])
def test_decode_image_base64_strips_data_url(prefix):
    """Test that data URL prefix is correctly stripped and decoded."""
    payload = b"test payload for decoding"
    encoded = base64.b64encode(payload).decode("utf-8")
    
    data_url = f"{prefix}{encoded}"
    assert decode_image_base64(data_url) == payload

@pytest.mark.parametrize("invalid_payload", [
    "this is not base64 @#$%^&*()",
    "data:image/png;base64,invalid_base_64!!!",
    "123", # Not proper length
])
def test_decode_image_base64_rejects_invalid_payload(invalid_payload):
    """Test that invalid base64 payloads raise ValueError."""
    with pytest.raises(ValueError, match="Invalid base64 image payload"):
        decode_image_base64(invalid_payload)

@pytest.mark.parametrize("input_str, expected", [
    ("data:image/jpeg;base64,ABCD", "ABCD"),
    ("data:image/png;base64,XYZ=", "XYZ="),
    ("data:application/pdf;base64,1234", "1234"),
    ("ABCD", "ABCD"),
    ("data:image/jpeg;base64,data:image/png;base64,ABCD", "data:image/png;base64,ABCD"),
    ("", ""),
])
def test_strip_data_url_plain_and_prefixed(input_str, expected):
    """Test extraction of base64 content from data URLs."""
    assert _strip_data_url(input_str) == expected

@pytest.mark.parametrize("base64_str, expected_bytes", [
    ("ABCD", 3),
    ("ABC=", 2),
    ("AB==", 1),
    ("", 0),
    ("A" * 100, 75),
    ("A" * 100 + "==", 74),
])
def test_estimate_base64_bytes_padding_cases(base64_str, expected_bytes):
    """Test the estimation of base64 byte size based on string length and padding."""
    assert _estimate_base64_bytes(base64_str) == expected_bytes
