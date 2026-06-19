"""Image preprocessing and optimization utilities."""

from __future__ import annotations

import io
import logging
from typing import Optional
from PIL import Image

_LOGGER = logging.getLogger(__name__)

# Image constraints
MAX_IMAGE_DIMENSION = 4096
MIN_IMAGE_DIMENSION = 100
QUALITY_THRESHOLD = 50


def validate_and_preprocess_image(image_bytes: bytes) -> Optional[Image.Image]:
    """Validate image format and preprocess for better recognition.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        PIL Image object ready for processing, or None if invalid
        
    Raises:
        ValueError: If image is invalid
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Validate image format
        if image.format not in ("JPEG", "PNG", "WEBP", "BMP", "GIF"):
            raise ValueError(f"Unsupported image format: {image.format}")
        
        # Validate dimensions
        width, height = image.size
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise ValueError(f"Image too small: {width}x{height} (min {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION})")
        
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            _LOGGER.warning("Image dimensions exceed optimal size: %sx%s, may be resized", width, height)
        
        # Convert RGBA to RGB if needed (Gemini Vision prefers RGB)
        if image.mode in ("RGBA", "LA", "P"):
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = rgb_image
        elif image.mode != "RGB":
            image = image.convert("RGB")
        
        _LOGGER.debug("Image validated and preprocessed: %sx%s, mode=%s", width, height, image.mode)
        return image
        
    except (OSError, IOError) as e:
        raise ValueError(f"Invalid image file: {e}")


def optimize_image_for_api(image: Image.Image, max_size: tuple = (2048, 2048)) -> Image.Image:
    """Optimize image for API processing.
    
    Args:
        image: PIL Image object
        max_size: Maximum dimensions (width, height)
        
    Returns:
        Optimized PIL Image
    """
    width, height = image.size
    
    # Resize if too large
    if width > max_size[0] or height > max_size[1]:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        _LOGGER.debug("Image resized for API: %sx%s", image.width, image.height)
    
    return image


def get_image_quality_estimate(image: Image.Image) -> float:
    """Estimate image quality (0-100).
    
    Based on:
    - Resolution
    - Color mode
    - Size
    
    Args:
        image: PIL Image object
        
    Returns:
        Quality score 0-100
    """
    width, height = image.size
    
    # Base score from resolution. The old scale was megapixels * 10, which made
    # normal 720p/1080p mobile images look "very low quality" even when usable.
    megapixels = (width * height) / 1_000_000
    short_side = min(width, height)
    if short_side < MIN_IMAGE_DIMENSION:
        resolution_score = 0
    elif megapixels < 0.08:
        resolution_score = 20
    elif megapixels < 0.30:
        resolution_score = 38
    else:
        resolution_score = min(100, 45 + megapixels * 32)
    
    # Penalty for unusual modes
    mode_penalty = 0
    if image.mode != "RGB":
        mode_penalty = 10
    
    # Penalty for extreme aspect ratios
    aspect_ratio = max(width, height) / min(width, height)
    aspect_penalty = max(0, (aspect_ratio - 2) * 8)
    
    quality = resolution_score - mode_penalty - aspect_penalty
    return max(0, min(100, quality))
