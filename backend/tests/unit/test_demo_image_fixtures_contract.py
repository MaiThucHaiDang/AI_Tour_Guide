import base64
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.vision.image_recognition import recognize_image
from utils.image_utils import (
    MIN_IMAGE_DIMENSION,
    get_image_quality_estimate,
    optimize_image_for_api,
    validate_and_preprocess_image,
)


FIXTURE_IMAGE_DIR = Path(__file__).resolve().parents[3] / "test_images"


@pytest.mark.parametrize("fixture_name", ["kientrung.jpg", "duyet_thi_duong.jpg"])
def test_demo_fixture_image_can_enter_vision_pipeline(fixture_name):
    image_path = FIXTURE_IMAGE_DIR / fixture_name
    assert image_path.exists(), f"Missing image fixture: {image_path}"

    image = validate_and_preprocess_image(image_path.read_bytes())
    assert image.mode == "RGB"
    assert min(image.size) >= MIN_IMAGE_DIMENSION

    optimized = optimize_image_for_api(image.copy())
    assert optimized.size[0] <= 2048
    assert optimized.size[1] <= 2048
    assert get_image_quality_estimate(optimized) > 30


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fixture_name,artifact_id,artifact_name",
    [
        ("kientrung.jpg", "kien-trung", "Điện Kiến Trung"),
        ("duyet_thi_duong.jpg", "duyet-thi-duong", "Duyệt Thị Đường"),
    ],
)
@patch("services.vision.image_recognition.find_artifact_by_name")
@patch("services.vision.image_recognition._load_feature_catalog")
@patch("services.vision.image_recognition._get_vision_providers")
async def test_demo_fixture_image_recognition_contract_with_mocked_ai_provider(
    mock_get_providers,
    mock_load_catalog,
    mock_find_artifact,
    fixture_name,
    artifact_id,
    artifact_name,
):
    image_path = FIXTURE_IMAGE_DIR / fixture_name
    assert image_path.exists(), f"Missing image fixture: {image_path}"

    fake_response = MagicMock()
    fake_response.text = json.dumps({
        "artifact_name": artifact_name,
        "confidence": 0.96,
        "is_historical_artifact": True,
        "recognition_type": "building",
        "visible_features": ["mái ngói", "kiến trúc cung đình"],
        "visual_summary": f"Ảnh chụp {artifact_name}.",
        "top_candidates": [
            {
                "artifact_name": artifact_name,
                "confidence": 0.96,
                "visible_features": ["mái ngói", "kiến trúc cung đình"],
                "evidence": "Có các chi tiết kiến trúc cung đình rõ."
            }
        ],
    })

    mock_model = MagicMock()
    mock_model.aio.models.generate_content = AsyncMock(return_value=fake_response)
    mock_get_providers.return_value = [("gemini_key_1", mock_model)]
    mock_find_artifact.return_value = SimpleNamespace(
        art_id=artifact_id,
        name_vi=artifact_name,
        name_en=artifact_name,
    )
    mock_load_catalog.return_value = {
        artifact_id: {
            "name_vi": artifact_name,
            "aliases_vi": [artifact_name],
            "whole_building_features": ["mái ngói", "kiến trúc cung đình"],
        }
    }

    image_base64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    result = await recognize_image(image_base64, lang="vi", lat=16.46, lng=107.58)

    assert result.recognized is True
    assert result.artifact_id == artifact_id
    assert result.raw_label == artifact_name
    assert result.confidence_score == 0.96
    assert result.final_score >= 0.7
    assert result.needs_user_confirmation is False
    mock_model.aio.models.generate_content.assert_awaited_once()
