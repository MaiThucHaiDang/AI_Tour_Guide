import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.repositories.artifact_repository import (
    _normalize_text,
    _canonical_tokens,
    _replace_canonical_phrases,
    _replace_fuzzy_canonical_phrases,
    _replace_token_window,
    _replace_fuzzy_token_window,
    _replace_canonical_tokens,
    _replace_fuzzy_canonical_tokens,
    _is_fuzzy_phrase_match,
    _is_fuzzy_token_match,
    _token_similarity,
    _levenshtein_distance,
    _tokenize_query,
    canonicalize_transcript_entities,
    find_artifact_by_name,
    get_artifact_context,
    get_artifact_context_by_id,
    graph_augmented_search,
)
from models.artifact import Artifact
from models.location import Location

def test_repo_normalize_text_removes_vietnamese_diacritics():
    """normalize đúng"""
    assert _normalize_text("Ngọ Môn Huế") == "ngo mon hue"
    assert _normalize_text("Đại Nội") == "dai noi"

def test_canonical_tokens_removes_noise_and_splits():
    """token list đúng"""
    tokens = _canonical_tokens("Ngọ Môn Huế")
    assert tokens == ["Ngọ", "Môn", "Huế"]

def test_replace_canonical_phrases_exact():
    """thay cụm đúng"""
    text = "Toi dang o ngo mon hue"
    phrases = ["Ngọ Môn Huế"]
    res = _replace_canonical_phrases(text, phrases)
    assert res == "Toi dang o Ngọ Môn Huế"

def test_replace_fuzzy_canonical_phrases_near_sound():
    """sửa lỗi gần âm"""
    text = "ngot mon huen"
    phrases = ["Ngọ Môn Huế"]
    res = _replace_fuzzy_canonical_phrases(text, phrases)
    assert res == "Ngọ Môn Huế"

def test_replace_token_window_exact_sequence():
    """thay đúng sequence"""
    text = "hello ngo mon hue world"
    res = _replace_token_window(text, ["ngo", "mon", "hue"], "Ngọ Môn Huế")
    assert res == "hello Ngọ Môn Huế world"

def test_replace_fuzzy_token_window_handles_missing_diacritics():
    """thay fuzzy"""
    text = "hello ngot mon huen world"
    res = _replace_fuzzy_token_window(text, ["ngo", "mon", "hue"], "Ngọ Môn Huế")
    assert res == "hello Ngọ Môn Huế world"

def test_replace_canonical_tokens_exact():
    """token chính tả đúng"""
    text = "tham quan ngo"
    tokens = ["Ngọ"]
    res = _replace_canonical_tokens(text, tokens)
    assert res == "tham quan Ngọ"

def test_replace_fuzzy_canonical_tokens_near_sound():
    """token gần âm đúng"""
    text = "tham quan ngot"
    tokens = ["Ngọ"]
    res = _replace_fuzzy_canonical_tokens(text, tokens)
    assert res == "tham quan Ngọ"

def test_is_fuzzy_phrase_match_threshold():
    """true/false đúng"""
    assert _is_fuzzy_phrase_match(["ngot", "mon", "huen"], ["ngo", "mon", "hue"]) is True
    assert _is_fuzzy_phrase_match(["xyz", "abc", "def"], ["ngo", "mon", "hue"]) is False

def test_is_fuzzy_token_match_short_token_strict():
    """token ngắn không match sai"""
    assert _is_fuzzy_token_match("ngo", "ngot") is True
    assert _is_fuzzy_token_match("abc", "xyz") is False

def test_token_similarity_range():
    """0..1"""
    assert _token_similarity("ngo", "ngo") == 1.0
    assert _token_similarity("kitten", "sitting") == 1.0 - (3/7)

def test_levenshtein_distance_known_pairs():
    """kitten/sitting = 3"""
    assert _levenshtein_distance("kitten", "sitting") == 3
    assert _levenshtein_distance("", "abc") == 3

def test_tokenize_query_filters_short_noise():
    """token đúng"""
    tokens = _tokenize_query("xin chao cac ban, cho toi biet ve ngo mon hue")
    assert "ngo" in tokens
    assert "mon" in tokens
    assert "hue" in tokens
    assert "ban" not in tokens

@pytest.fixture
def mock_session():
    mock = AsyncMock()
    mock.return_value.__aenter__.return_value = mock
    mock.return_value.__aexit__.return_value = None
    return mock

@pytest.mark.asyncio
@patch("backend.repositories.artifact_repository.async_session_factory")
async def test_canonicalize_transcript_entities_fix_ngo_mon_hue(mock_factory, mock_session):
    """sửa ngo mon hue"""
    mock_factory.return_value = mock_session.return_value
    
    art = Artifact(name_vi="Ngọ Môn Huế", name_en="Hue Ngo Mon")
    loc = Location(name_vi="Đại Nội", name_en="Imperial City")
    
    mock_art_result = MagicMock()
    mock_art_result.scalars.return_value.all.return_value = [art]
    
    mock_loc_result = MagicMock()
    mock_loc_result.scalars.return_value.all.return_value = [loc]
    
    mock_session.execute = AsyncMock(side_effect=[mock_art_result, mock_loc_result])
    
    text = "ngot mon huen dep lam"
    res = await canonicalize_transcript_entities(text, "vi")
    assert "Ngọ Môn Huế" in res

@pytest.mark.asyncio
@patch("backend.repositories.artifact_repository._fetch_bilingual_fields", new_callable=AsyncMock)
@patch("backend.repositories.artifact_repository.async_session_factory")
async def test_find_artifact_by_name_exact_vi_en(mock_factory, mock_fetch, mock_session):
    """tìm đúng"""
    mock_factory.return_value = mock_session.return_value
    mock_fetch.return_value = {"history_text_vi": "vi", "history_text_en": "en"}
    
    art = Artifact(art_id=1, loc_id=1, name_vi="Ngọ Môn", name_en="Ngo Mon Gate", history_text_vi="vi", history_text_en="en")
    
    mock_loc_result = MagicMock()
    mock_loc_result.scalars.return_value.first.return_value = None
    
    mock_art_result = MagicMock()
    mock_art_result.scalars.return_value.all.return_value = [art]
    mock_art_result.scalars.return_value.first.return_value = art
    
    mock_session.execute = AsyncMock(side_effect=[mock_loc_result, mock_art_result])
    
    res = await find_artifact_by_name("Ngọ Môn")
    assert res is not None
    assert res.name_vi == "Ngọ Môn"

@pytest.mark.asyncio
@patch("backend.repositories.artifact_repository._fetch_bilingual_fields", new_callable=AsyncMock)
@patch("backend.repositories.artifact_repository.async_session_factory")
async def test_find_artifact_by_name_fuzzy_accentless(mock_factory, mock_fetch, mock_session):
    """tìm dien kien trung"""
    mock_factory.return_value = mock_session.return_value
    mock_fetch.return_value = {"history_text_vi": "vi", "history_text_en": "en"}
    
    art = Artifact(art_id=1, loc_id=1, name_vi="Điện Kiến Trung", name_en="Kien Trung Palace", history_text_vi="vi", history_text_en="en")
    
    async def custom_execute(stmt, *args, **kwargs):
        mock_res = MagicMock()
        if "location" in str(stmt).lower():
            mock_res.scalars.return_value.first.return_value = None
            mock_res.scalars.return_value.all.return_value = []
        else:
            mock_res.scalars.return_value.first.return_value = art
            mock_res.scalars.return_value.all.return_value = [art]
        return mock_res
        
    mock_session.execute = AsyncMock(side_effect=custom_execute)
    
    res = await find_artifact_by_name("dien kien trung")
    assert res is not None
    assert res.name_vi == "Điện Kiến Trung"

@pytest.mark.asyncio
@patch("backend.repositories.artifact_repository.async_session_factory")
async def test_get_artifact_context_returns_no_match_message(mock_factory, mock_session):
    """không 500 khi miss"""
    mock_factory.return_value = mock_session.return_value
    
    mock_art_res = MagicMock()
    mock_art_res.scalars.return_value.all.return_value = []
    
    mock_session.execute = AsyncMock(return_value=mock_art_res)
    
    res = await get_artifact_context("unknown query xyz", "history_text_vi")
    assert res == "No matching artifact found in database."

@pytest.mark.asyncio
@patch("backend.repositories.artifact_repository.async_session_factory")
async def test_get_artifact_context_by_id_invalid_id(mock_factory, mock_session):
    """fallback rõ ràng"""
    mock_factory.return_value = mock_session.return_value
    
    res = await get_artifact_context_by_id("abc", "history_text_vi")
    assert res == "Database is temporarily unavailable."

@pytest.mark.asyncio
@patch("backend.repositories.artifact_repository.EmbeddingService.get_embedding", new_callable=AsyncMock)
@patch("backend.repositories.artifact_repository._fetch_bilingual_fields", new_callable=AsyncMock)
@patch("backend.repositories.artifact_repository.async_session_factory")
async def test_graph_augmented_search_returns_top_k_and_facts(mock_factory, mock_fetch, mock_get_embedding, mock_session):
    """số lượng <= top_k"""
    mock_factory.return_value = mock_session.return_value
    mock_fetch.return_value = {"history_text_vi": "vi", "history_text_en": "en"}
    mock_get_embedding.return_value = [0.1] * 384
    
    mock_entry_res = MagicMock()
    mock_entry_res.scalars.return_value.all.return_value = [1]
    
    mock_rel_res = MagicMock()
    mock_rel_res.scalars.return_value.all.return_value = [2, 3]
    
    art1 = Artifact(art_id=1, loc_id=1, name_vi="A", name_en="A", history_text_vi="vi", history_text_en="en")
    art2 = Artifact(art_id=2, loc_id=1, name_vi="B", name_en="B", history_text_vi="vi", history_text_en="en")
    art3 = Artifact(art_id=3, loc_id=1, name_vi="C", name_en="C", history_text_vi="vi", history_text_en="en")
    
    mock_final_res = MagicMock()
    mock_final_res.scalars.return_value.all.return_value = [art1, art2, art3]
    
    mock_session.execute = AsyncMock(side_effect=[mock_entry_res, mock_rel_res, mock_final_res])
    
    res = await graph_augmented_search("some query", top_k=3)
    assert len(res) <= 3
