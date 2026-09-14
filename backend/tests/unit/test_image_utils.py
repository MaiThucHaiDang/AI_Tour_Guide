import pytest
import io
from unittest.mock import MagicMock, patch
from PIL import Image

from utils.image_utils import (
    validate_and_preprocess_image,
    optimize_image_for_api,
    get_image_quality_estimate,
    MIN_IMAGE_DIMENSION,
    MAX_IMAGE_DIMENSION,
)

# --- Helper functions to create real test bytes if needed ---

def create_test_image(format="JPEG", mode="RGB", size=(200, 200), color=(255, 0, 0)):
    img = Image.new(mode, size, color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    return img_bytes.getvalue()


# --- Tests for validate_and_preprocess_image ---

@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP", "BMP", "GIF"])
@patch("utils.image_utils.Image.open")
def test_validate_image_accepts_valid_formats(mock_open, fmt):
    """Test that all supported formats are accepted. Mocks Image.open."""
    mock_img = MagicMock()
    mock_img.format = fmt
    mock_img.size = (200, 200)
    mock_img.mode = "RGB"
    mock_open.return_value = mock_img

    result = validate_and_preprocess_image(b"dummy_bytes")
    
    assert result is mock_img
    mock_open.assert_called_once()

@patch("utils.image_utils.Image.open")
def test_validate_image_rejects_unsupported_format(mock_open):
    """Test that unsupported formats like TIFF are rejected."""
    mock_img = MagicMock()
    mock_img.format = "TIFF"
    mock_img.size = (200, 200)
    mock_open.return_value = mock_img

    with pytest.raises(ValueError, match="Unsupported image format: TIFF"):
        validate_and_preprocess_image(b"dummy_bytes")

def test_validate_image_rejects_non_image_bytes():
    """Test with real invalid bytes to trigger IOError/OSError."""
    with pytest.raises(ValueError, match="Invalid image file"):
        validate_and_preprocess_image(b"not an image file content")

@pytest.mark.parametrize("width,height", [
    (MIN_IMAGE_DIMENSION - 1, 200),
    (200, MIN_IMAGE_DIMENSION - 1),
    (10, 10),
])
@patch("utils.image_utils.Image.open")
def test_validate_image_rejects_too_small(mock_open, width, height):
    """Test that images smaller than MIN_IMAGE_DIMENSION are rejected."""
    mock_img = MagicMock()
    mock_img.format = "JPEG"
    mock_img.size = (width, height)
    mock_open.return_value = mock_img

    with pytest.raises(ValueError, match="Image too small"):
        validate_and_preprocess_image(b"dummy_bytes")

@patch("utils.image_utils._LOGGER.warning")
@patch("utils.image_utils.Image.open")
def test_validate_image_warns_on_large_image(mock_open, mock_warning):
    """Test that large images log a warning but are still accepted."""
    mock_img = MagicMock()
    mock_img.format = "JPEG"
    mock_img.size = (MAX_IMAGE_DIMENSION + 1, MAX_IMAGE_DIMENSION + 1)
    mock_img.mode = "RGB"
    mock_open.return_value = mock_img

    result = validate_and_preprocess_image(b"dummy_bytes")
    
    assert result is mock_img
    mock_warning.assert_called_once()
    assert "exceed optimal size" in mock_warning.call_args[0][0]

@pytest.mark.parametrize("rgba_mode", ["RGBA", "LA", "P"])
@patch("utils.image_utils.Image.new")
@patch("utils.image_utils.Image.open")
def test_validate_image_converts_rgba_to_rgb(mock_open, mock_new, rgba_mode):
    """Test conversion of RGBA/LA/P to RGB with pasting."""
    mock_img = MagicMock()
    mock_img.format = "PNG"
    mock_img.size = (200, 200)
    mock_img.mode = rgba_mode
    mock_img.split.return_value = [MagicMock()] * 4 # Mock split returning channels
    mock_open.return_value = mock_img

    mock_rgb_img = MagicMock()
    mock_new.return_value = mock_rgb_img

    result = validate_and_preprocess_image(b"dummy_bytes")

    assert result is mock_rgb_img
    mock_new.assert_called_once_with("RGB", (200, 200), (255, 255, 255))
    mock_rgb_img.paste.assert_called_once()

@patch("utils.image_utils.Image.open")
def test_validate_image_converts_other_modes(mock_open):
    """Test conversion of other modes (like L, CMYK) to RGB."""
    mock_img = MagicMock()
    mock_img.format = "JPEG"
    mock_img.size = (200, 200)
    mock_img.mode = "CMYK"
    mock_converted = MagicMock()
    mock_img.convert.return_value = mock_converted
    mock_open.return_value = mock_img

    result = validate_and_preprocess_image(b"dummy_bytes")

    assert result is mock_converted
    mock_img.convert.assert_called_once_with("RGB")


# --- Tests for optimize_image_for_api ---

def test_optimize_image_resizes_large_input():
    """Test that an image larger than max_size is resized."""
    mock_img = MagicMock()
    mock_img.size = (3000, 2000)
    
    # We mock thumbnail since it works in-place
    optimize_image_for_api(mock_img, max_size=(2048, 2048))
    
    mock_img.thumbnail.assert_called_once_with((2048, 2048), Image.Resampling.LANCZOS)

def test_optimize_image_keeps_small_input():
    """Test that an image smaller than max_size is not resized."""
    mock_img = MagicMock()
    mock_img.size = (800, 600)
    
    optimize_image_for_api(mock_img, max_size=(2048, 2048))
    
    # Since condition `width > max_size[0] or height > max_size[1]` is false
    mock_img.thumbnail.assert_not_called()


# --- Tests for get_image_quality_estimate ---

@pytest.mark.parametrize("width,height,expected_score", [
    (50, 50, 0),         # Tiny image under min dimension -> score 0
])
def test_quality_low_for_tiny(width, height, expected_score):
    """Test quality score for extremely small images."""
    mock_img = MagicMock()
    mock_img.size = (width, height)
    mock_img.mode = "RGB"
    
    assert get_image_quality_estimate(mock_img) == expected_score

@pytest.mark.parametrize("width,height,mode,is_extreme_aspect", [
    (2000, 200, "RGB", True),    # Extreme aspect ratio (10:1)
    (800, 600, "CMYK", False),   # Non-RGB mode penalty
])
def test_quality_penalties(width, height, mode, is_extreme_aspect):
    """Test quality score penalties for bad aspect ratios and modes."""
    mock_img = MagicMock()
    mock_img.size = (width, height)
    mock_img.mode = mode
    
    score = get_image_quality_estimate(mock_img)
    if is_extreme_aspect:
        assert score < 50
    else:
        # 800x600 = 0.48 MP. Expected base score: 45 + 0.48*32 = 60.36
        # Penalty for CMYK: 10. Total expected ~ 50.36
        assert 50 <= score <= 51

def test_quality_high_for_normal_mobile_photo():
    """Test quality score for a standard high-res photo."""
    mock_img = MagicMock()
    mock_img.size = (1920, 1080) # ~2.07 MP
    mock_img.mode = "RGB"
    
    score = get_image_quality_estimate(mock_img)
    # 2.07 * 32 + 45 = 111.24, maxed at 100
    assert score == 100
