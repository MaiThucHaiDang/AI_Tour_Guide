import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from schemas.vision import VisionResult
from services.vision.image_recognition import (
    _normalize_text,
    _coerce_feature_list,
    _coerce_candidates,
    _feature_terms_for,
    _name_alias_match_score,
    _visual_feature_score,
    _gps_score,
    _final_candidate_score,
    _match_best_candidate,
    _generate_vision_content,
    recognize_image,
)
from core.config import settings

# 1
def test_vision_normalize_text_removes_accents_and_symbols():
    assert _normalize_text("Điện Kiến Trung!") == "dien kien trung"
    assert _normalize_text("  Ngọ Môn (Huế)  ") == "ngo mon hue"
    assert _normalize_text(None) == ""

# 2
def test_coerce_feature_list_accepts_list_and_csv():
    assert _coerce_feature_list([" a ", "b", "", None]) == ["a", "b", "None"]
    assert _coerce_feature_list("Mái ngói, Cột gỗ ; Điêu khắc rồng") == ["Mái ngói", "Cột gỗ", "Điêu khắc rồng"]
    assert _coerce_feature_list(None) == []

# 3
def test_coerce_candidates_uses_primary_candidate_when_no_array():
    data = {
        "visual_summary": "Primary evidence"
    }
    candidates = _coerce_candidates(data, label="Ngọ Môn", confidence=0.85, visual_features="Cột cờ")
    assert len(candidates) == 1
    assert candidates[0]["artifact_name"] == "Ngọ Môn"
    assert candidates[0]["confidence"] == 0.85
    assert candidates[0]["visible_features"] == ["Cột cờ"]
    assert candidates[0]["evidence"] == "Primary evidence"

# 4
def test_coerce_candidates_limits_to_five():
    data = {
        "top_candidates": [
            {"artifact_name": "A", "confidence": 0.9},
            {"artifact_name": "B", "confidence": 0.8},
            {"artifact_name": "C", "confidence": 0.7},
            {"artifact_name": "D", "confidence": 0.6},
            {"artifact_name": "E", "confidence": 0.5},
            {"artifact_name": "F", "confidence": 0.4},
        ]
    }
    candidates = _coerce_candidates(data, label="A", confidence=0.9, visual_features="")
    assert len(candidates) == 5
    names = [c["artifact_name"] for c in candidates]
    assert "F" not in names

# 5
def test_feature_terms_for_detail_prioritizes_detail_fields():
    item = {
        "architectural_details": ["chạm rồng", "cột gỗ"],
        "whole_building_features": ["mái lợp ngói"]
    }
    terms = _feature_terms_for(item, "architectural_detail")
    assert terms[0] == "chạm rồng"
    assert terms[1] == "cột gỗ"
    assert terms[2] == "mái lợp ngói"
    
    terms_normal = _feature_terms_for(item, "building")
    assert terms_normal[0] == "mái lợp ngói"

# 6
def test_name_alias_exact_alias_scores_one():
    class MockArtifactInfo:
        name_vi = "Ngọ Môn"
        name_en = "Ngo Mon Gate"
    
    feature_item = {
        "aliases_vi": ["Cửa chính", "Nam khuyết đài"]
    }
    
    score = _name_alias_match_score(MockArtifactInfo(), feature_item, "Nam khuyết đài")
    assert score == 1.0

# 7
def test_name_alias_partial_overlap_scores_below_exact():
    class MockArtifactInfo:
        name_vi = "Điện Thái Hòa"
        name_en = "Thai Hoa Palace"
    
    feature_item = {}
    score = _name_alias_match_score(MockArtifactInfo(), feature_item, "Thái Hòa")
    # Substring match -> 0.85
    assert score == 0.85
    
    score_token = _name_alias_match_score(MockArtifactInfo(), feature_item, "Điện của nhà vua Thái")
    assert 0 < score_token <= 0.75

# 8
def test_visual_feature_score_matches_visible_evidence():
    feature_item = {
        "whole_building_features": ["mái lợp ngói hoàng lưu ly", "cột trụ đỏ"],
        "architectural_details": ["chạm khắc rồng"]
    }
    candidate = {
        "visible_features": ["ngói vàng", "cột màu đỏ"],
        "evidence": "Tôi thấy có cột trụ đỏ và mái lợp ngói hoàng lưu ly rất đẹp."
    }
    
    score = _visual_feature_score(feature_item, candidate, "architecture")
    assert score > 0.0

# 9
def test_visual_feature_score_returns_zero_without_catalog_item():
    candidate = {
        "visible_features": ["ngói vàng", "cột màu đỏ"],
        "evidence": "Tôi thấy có cột trụ đỏ"
    }
    score = _visual_feature_score(None, candidate, "architecture")
    assert score == 0.0

# 10
def test_gps_score_half_without_coordinates():
    assert _gps_score(None, None) == 0.5
    assert _gps_score(16.4, None) == 0.5

# 11
def test_gps_score_one_with_coordinates():
    assert _gps_score(16.4, 107.5) == 1.0

# 12
def test_final_candidate_score_whole_building_weights_confidence_name_features_gps():
    candidate = {"confidence": 0.9, "artifact_name": "Ngọ Môn", "visible_features": ["a"], "evidence": "b"}
    artifact_info = MagicMock(name_vi="Ngọ Môn")
    feature_item = {"whole_building_features": ["b"]}
    
    score = _final_candidate_score(candidate, artifact_info, feature_item, "building", 16.4, 107.5)
    # 0.9 * 0.4 + 1.0 * 0.25 + score_vis * 0.2 + 1.0 * 0.15 = 0.36 + 0.25 + 0.2 + 0.15 = 0.96
    assert 0.0 <= score <= 1.0
    assert score > 0.8

# 13
def test_final_candidate_score_detail_weights_visual_more():
    candidate = {"confidence": 0.9, "artifact_name": "Ngọ Môn", "visible_features": ["a"], "evidence": "b"}
    artifact_info = MagicMock(name_vi="Ngọ Môn")
    feature_item = {"architectural_details": ["b"]}
    
    # Detail weights: confidence 0.35, alias 0.20, visual 0.35, gps 0.10
    score_detail = _final_candidate_score(candidate, artifact_info, feature_item, "architectural_detail", 16.4, 107.5)
    
    assert 0.0 <= score_detail <= 1.0
    # visual feature match is 1 / min(1, 5) = 1.0
    # 0.9*0.35 + 1.0*0.2 + 1.0*0.35 + 1.0*0.1 = 0.315 + 0.2 + 0.35 + 0.1 = 0.965
    assert abs(score_detail - 0.965) < 0.01

# 14
@pytest.mark.asyncio
@patch("services.vision.image_recognition.find_artifact_by_name")
@patch("services.vision.image_recognition._load_feature_catalog")
async def test_match_best_candidate_uses_repository_artifact_match(mock_load_catalog, mock_find):
    mock_load_catalog.return_value = {"123": {"whole_building_features": ["Cột cờ"]}}
    artifact_info = MagicMock(art_id="123", name_vi="Ngọ Môn")
    mock_find.return_value = artifact_info
    
    candidates = [{"artifact_name": "Ngọ Môn", "confidence": 0.9}]
    best_info, best_label, best_score, scored_candidates = await _match_best_candidate(candidates, "building", 16.4, 107.5)
    
    assert best_info == artifact_info
    assert best_label == "Ngọ Môn"
    assert best_score > 0
    assert len(scored_candidates) == 1

# 15
@pytest.mark.asyncio
@patch("services.vision.image_recognition.find_artifact_by_name")
@patch("services.vision.image_recognition.map_vision_label_to_artifact_id")
@patch("services.vision.image_recognition._load_feature_catalog")
async def test_match_best_candidate_falls_back_legacy_mapping(mock_load_catalog, mock_map, mock_find):
    mock_load_catalog.return_value = {}
    mock_find.side_effect = [None, MagicMock(art_id="999", name_vi="Lăng Minh Mạng")] 
    mock_map.return_value = "999"
    
    candidates = [{"artifact_name": "Tomb of Minh Mang", "confidence": 0.8}]
    best_info, best_label, best_score, scored_candidates = await _match_best_candidate(candidates, "building", None, None)
    
    assert best_info is not None
    assert best_info.art_id == "999"
    assert best_label == "Tomb of Minh Mang"
    assert scored_candidates[0]["artifact_id"] == "999"

# 16
@pytest.mark.asyncio
@patch("services.vision.image_recognition.find_artifact_by_name")
@patch("services.vision.image_recognition._load_feature_catalog")
async def test_match_best_candidate_returns_scored_candidates(mock_load_catalog, mock_find):
    mock_load_catalog.return_value = {}
    mock_find.side_effect = [MagicMock(art_id="1"), MagicMock(art_id="2")]
    
    candidates = [
        {"artifact_name": "Art 1", "confidence": 0.9},
        {"artifact_name": "Art 2", "confidence": 0.8}
    ]
    _, _, _, scored_candidates = await _match_best_candidate(candidates, "building", None, None)
    assert len(scored_candidates) == 2
    assert "final_score" in scored_candidates[0]
    assert "final_score" in scored_candidates[1]

@pytest.fixture
def mock_vision_deps():
    with patch('services.vision.image_recognition.validate_image_base64_size') as m1, \
         patch('services.vision.image_recognition.decode_image_base64', return_value=b'img') as m2, \
         patch('services.vision.image_recognition.validate_and_preprocess_image', return_value=MagicMock()) as m3, \
         patch('services.vision.image_recognition.optimize_image_for_api', return_value=MagicMock()) as m4, \
         patch('services.vision.image_recognition.get_image_quality_estimate', return_value=100.0) as m5, \
         patch('services.vision.image_recognition._get_vision_providers') as mock_providers, \
         patch('services.vision.image_recognition.find_artifact_by_name') as mock_find_artifact:
        mock_model = MagicMock()
        mock_providers.return_value = [("gemini_key_1", mock_model)]
        yield mock_model, mock_find_artifact, m3

# 17
@pytest.mark.asyncio
async def test_recognize_image_rejects_invalid_base64(mock_vision_deps):
    _, _, mock_preprocess = mock_vision_deps
    mock_preprocess.side_effect = ValueError("Invalid base64 format")
    
    res = await recognize_image("bad_base64")
    assert res.recognized is False
    assert res.error == "INVALID_IMAGE"

# 18
@pytest.mark.asyncio
async def test_recognize_image_rejects_non_artifact(mock_vision_deps):
    mock_model, _, _ = mock_vision_deps
    fake_response = MagicMock()
    fake_response.text = json.dumps({
        "artifact_name": "Modern car",
        "confidence": 0.95,
        "is_historical_artifact": False
    })
    mock_gen_content = AsyncMock(return_value=fake_response)
    mock_model.aio.models.generate_content = mock_gen_content

    res = await recognize_image("base64")
    assert res.recognized is False
    assert res.error == "NOT_AN_ARTIFACT"

# 19
@pytest.mark.asyncio
async def test_recognize_image_rejects_low_confidence(mock_vision_deps):
    mock_model, _, _ = mock_vision_deps
    fake_response = MagicMock()
    fake_response.text = json.dumps({
        "artifact_name": "Ngọ Môn",
        "confidence": 0.1,  # threshold is usually 0.5+
        "is_historical_artifact": True
    })
    mock_gen_content = AsyncMock(return_value=fake_response)
    mock_model.aio.models.generate_content = mock_gen_content

    # Assume settings.VISION_CONFIDENCE_THRESHOLD = 0.5
    with patch("services.vision.image_recognition.settings") as mock_settings:
        mock_settings.VISION_CONFIDENCE_THRESHOLD = 0.5
        mock_settings.GEMINI_VISION_MODEL = "test_model"
        res = await recognize_image("base64")
        assert res.recognized is False
        assert res.error == "LOW_CONFIDENCE"
        assert res.needs_user_confirmation is True

# 20
@pytest.mark.asyncio
async def test_recognize_image_handles_empty_provider_response(mock_vision_deps):
    mock_model, _, _ = mock_vision_deps
    fake_response = MagicMock()
    fake_response.text = ""
    mock_gen_content = AsyncMock(return_value=fake_response)
    mock_model.aio.models.generate_content = mock_gen_content

    res = await recognize_image("base64")
    assert res.recognized is False
    assert res.error == "VISION_EMPTY_RESPONSE"

# 21
@pytest.mark.asyncio
async def test_recognize_image_handles_auth_rate_provider_errors(mock_vision_deps):
    mock_model, _, _ = mock_vision_deps
    mock_gen_content = AsyncMock(side_effect=Exception("401 Unauthorized"))
    mock_model.aio.models.generate_content = mock_gen_content
    
    res1 = await recognize_image("base64")
    assert res1.error == "VISION_AUTH_ERROR"

    mock_gen_content.side_effect = Exception("429 Too Many Requests")
    with patch("services.vision.image_recognition.asyncio.sleep", new_callable=AsyncMock):
        res2 = await recognize_image("base64")
        assert res2.error == "VISION_RATE_LIMITED"
        
    mock_gen_content.side_effect = Exception("503 Service Unavailable")
    with patch("services.vision.image_recognition.asyncio.sleep", new_callable=AsyncMock):
        res3 = await recognize_image("base64")
        assert res3.error == "VISION_PROVIDER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_generate_vision_content_falls_back_to_second_api_key():
    first_client = MagicMock()
    second_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = '{"artifact_name":"Ngọ Môn"}'
    first_client.aio.models.generate_content = AsyncMock(side_effect=Exception("503 Service Unavailable"))
    second_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    with patch(
        "services.vision.image_recognition._get_vision_providers",
        return_value=[("gemini_key_1", first_client), ("gemini_key_2", second_client)],
    ), patch(
        "services.vision.image_recognition._vision_next_client_index",
        0,
    ), patch("services.vision.image_recognition.settings") as mock_settings:
        mock_settings.GEMINI_VISION_MODEL = "same-vision-model"
        response = await _generate_vision_content("prompt", MagicMock())

    assert response == fake_response
    first_client.aio.models.generate_content.assert_awaited_once()
    second_client.aio.models.generate_content.assert_awaited_once()
    assert first_client.aio.models.generate_content.call_args.kwargs["model"] == "same-vision-model"
    assert second_client.aio.models.generate_content.call_args.kwargs["model"] == "same-vision-model"

# 22
@pytest.mark.asyncio
async def test_recognize_image_parses_json_code_fence(mock_vision_deps):
    mock_model, mock_find, _ = mock_vision_deps
    fake_response = MagicMock()
    fake_response.text = "```json\n" + json.dumps({
        "artifact_name": "Ngọ Môn",
        "confidence": 0.95,
        "is_historical_artifact": True
    }) + "\n```"
    mock_gen_content = AsyncMock(return_value=fake_response)
    mock_model.aio.models.generate_content = mock_gen_content
    
    mock_find.return_value = MagicMock(art_id="123", name_vi="Ngọ Môn")
    
    with patch("services.vision.image_recognition.settings") as mock_settings:
        mock_settings.VISION_CONFIDENCE_THRESHOLD = 0.5
        mock_settings.GEMINI_VISION_MODEL = "test_model"
        res = await recognize_image("base64")
        assert res.recognized is True
        assert res.artifact_id == "123"

# 23
@pytest.mark.asyncio
async def test_recognize_image_returns_confirmation_when_final_score_low(mock_vision_deps):
    mock_model, mock_find, _ = mock_vision_deps
    fake_response = MagicMock()
    # Provide moderate confidence, but poor match score -> low final_score
    fake_response.text = json.dumps({
        "artifact_name": "Cổng Ngọ Môn Lạ",
        "confidence": 0.65,
        "is_historical_artifact": True
    })
    mock_gen_content = AsyncMock(return_value=fake_response)
    mock_model.aio.models.generate_content = mock_gen_content
    
    # Return artifact, but the alias score and visual match will be poor leading to final score < 0.6
    mock_find.return_value = MagicMock(art_id="123", name_vi="Something Else entirely")
    
    with patch("services.vision.image_recognition.settings") as mock_settings:
        mock_settings.VISION_CONFIDENCE_THRESHOLD = 0.5
        mock_settings.GEMINI_VISION_MODEL = "test_model"
        with patch("services.vision.image_recognition._final_candidate_score", return_value=0.55):
            res = await recognize_image("base64")
            assert res.recognized is True
            assert res.needs_user_confirmation is True
