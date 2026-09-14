import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock
from backend.orchestrators.unified_orchestrator import (
    UnifiedOrchestrator,
    _evict_tts_cache,
    _TTS_RESULT_CACHE,
    _ANSWER_CACHE,
    _ARTIFACT_INTRO_CACHE,
    ANSWER_CACHE_MAX_SIZE,
    _TTS_RESULT_CACHE_MAX,
    _TTS_RESULT_TTL
)
from backend.schemas.vision import ArtifactInfo
from backend.services.memory.conversation_memory import ConversationMemory

@pytest.fixture
def memory_mock():
    return AsyncMock(spec=ConversationMemory)

@pytest.fixture
def orchestrator(memory_mock):
    # clear caches
    _TTS_RESULT_CACHE.clear()
    _ANSWER_CACHE.clear()
    _ARTIFACT_INTRO_CACHE.clear()
    
    return UnifiedOrchestrator(
        stt=None,
        llm=None,
        tts=None,
        memory=memory_mock
    )

@pytest.mark.asyncio
async def test_finalize_without_tts_saves_memory_and_steps(orchestrator, memory_mock):
    artifact = ArtifactInfo(art_id="1", loc_id="1", name_vi="Ngọ Môn", name_en="en", history_text_vi="vi", history_text_en="en")
    res = await orchestrator._finalize_without_tts(
        response_text="Hello",
        final_query="Xin chào",
        lang_code="vi",
        session_id="session123",
        artifact_info=artifact,
        artifact_id="1",
        artifact_name="Ngọ Môn",
        detected_lang="vi",
        answer_source="template",
        processing_steps=["step1"]
    )
    
    assert res.response_text == "Hello"
    assert res.answer_source == "template"
    assert "Đã dùng mẫu trả lời nhanh" in res.processing_steps
    assert memory_mock.add_turn.call_count == 2

@pytest.mark.asyncio
async def test_classify_context_intent_compare_keywords(orchestrator):
    llm_mock = AsyncMock()
    llm_mock.generate_response.return_value = "COMPARE_OR_REFER"
    orchestrator._get_llm = MagicMock(return_value=llm_mock)
    
    intent = await orchestrator._classify_context_intent("A", "B", "compare A and B", "vi")
    assert intent == "COMPARE_OR_REFER"

@pytest.mark.asyncio
async def test_classify_context_intent_defaults_switch(orchestrator):
    llm_mock = AsyncMock()
    llm_mock.generate_response.return_value = "SOMETHING_ELSE"
    orchestrator._get_llm = MagicMock(return_value=llm_mock)
    
    intent = await orchestrator._classify_context_intent("A", "B", "query", "vi")
    assert intent == "SWITCH"

def test_classify_query_type_intro_for_marker_prompt(orchestrator):
    assert orchestrator._classify_query_type("[user sent an image of Ngo Mon]", None) == "intro"
    assert orchestrator._classify_query_type("giới thiệu về ngọ môn", None) == "intro"
    assert orchestrator._classify_query_type("tour guide mode", None) == "intro"
    assert orchestrator._classify_query_type("[user sent a click]", None) == "intro"

def test_classify_query_type_followup_for_fact_question(orchestrator):
    assert orchestrator._classify_query_type("năm xây dựng ngọ môn", None) == "followup"
    assert orchestrator._classify_query_type("ai thiết kế nó?", None) == "followup"

def test_get_llm_uses_factory_lazily(memory_mock):
    factory = MagicMock()
    factory.return_value = "LLM_INSTANCE"
    orch = UnifiedOrchestrator(stt=None, llm=None, tts=None, memory=memory_mock, llm_factory=factory)
    assert factory.call_count == 0
    llm1 = orch._get_llm()
    llm2 = orch._get_llm()
    assert factory.call_count == 1
    assert llm1 == "LLM_INSTANCE"
    assert llm2 == "LLM_INSTANCE"

def test_get_tts_returns_none_without_factory(orchestrator):
    assert orchestrator._get_tts() is None

def test_build_direct_answer_year_author_location(orchestrator):
    artifact = ArtifactInfo(art_id="1", loc_id="1", name_vi="Ngọ Môn", name_en="Ngo Mon", year=1833, author="Minh Mạng", history_text_vi="vi", history_text_en="en")
    # Year
    assert "1833" in orchestrator._build_direct_answer(artifact, "ngọ môn được xây năm nào", "vi")
    assert "1833" in orchestrator._build_direct_answer(artifact, "what year was ngo mon built", "en")
    # Author
    assert "Minh Mạng" in orchestrator._build_direct_answer(artifact, "ai là tác giả ngọ môn", "vi")
    assert "Minh Mạng" in orchestrator._build_direct_answer(artifact, "who is the author of ngo mon", "en")
    # Location
    assert "Đại Nội" in orchestrator._build_direct_answer(artifact, "ngọ môn ở đâu", "vi")
    
    # Check invalid or missing info
    assert orchestrator._build_direct_answer(artifact, "kể về lịch sử ngọ môn", "vi") is None

@pytest.mark.asyncio
async def test_build_artifact_description_marker_intro_uses_intro_cache(orchestrator):
    artifact = ArtifactInfo(art_id="art1", loc_id="1", name_vi="Ngọ Môn", name_en="en", history_text_vi="vi", history_text_en="en")
    _ARTIFACT_INTRO_CACHE["art1"] = "Cached Intro"
    
    res = await orchestrator._build_artifact_description(artifact, "hướng dẫn viên ngọ môn", "vi")
    assert res == "Cached Intro"

@pytest.mark.asyncio
@patch("backend.orchestrators.unified_orchestrator.get_settings")
async def test_generate_intro_uses_voice_prompt_and_sanitizes(mock_settings, orchestrator):
    mock_settings.return_value.LLM_MAX_TOKENS = 100
    llm_mock = AsyncMock()
    llm_mock.generate_response.return_value = "DB_CONTEXT: Here is the intro."
    orchestrator._get_llm = MagicMock(return_value=llm_mock)
    
    artifact = ArtifactInfo(art_id="art1", loc_id="1", name_vi="Ngọ Môn", name_en="en", history_text_vi="vi", history_text_en="en")
    intro = await orchestrator._generate_intro(artifact, "vi")
    # Due to _sanitize_user_response
    assert "tư liệu về di tích" in intro or "Here is the intro" in intro

def test_wrapped_summary_vi_en_and_missing_history(orchestrator):
    artifact = ArtifactInfo(art_id="1", loc_id="1", name_vi="Ngọ Môn", history_text_vi="", name_en="Ngo Mon", history_text_en="")
    assert "chưa có dữ liệu" in orchestrator._wrapped_summary(artifact, "vi")
    assert "no data available" in orchestrator._wrapped_summary(artifact, "en")
    
    artifact.history_text_vi = "Lịch sử dài."
    artifact.history_text_en = "Long history."
    assert "Lịch sử dài." in orchestrator._wrapped_summary(artifact, "vi")
    assert "Long history." in orchestrator._wrapped_summary(artifact, "en")

@pytest.mark.asyncio
@patch("backend.orchestrators.unified_orchestrator.find_artifact_by_name")
async def test_find_multi_artifacts_with_va_and_and_separators(mock_find, orchestrator):
    mock_find.side_effect = lambda n: ArtifactInfo(art_id=n, loc_id="1", name_vi=n, name_en="en", history_text_vi="vi", history_text_en="en") if "a" in n or "b" in n else None
    
    res_va = await orchestrator._find_multi_artifacts("a va b")
    assert len(res_va) == 2
    
    res_and = await orchestrator._find_multi_artifacts("a and b")
    assert len(res_and) == 2
    
    res_amp = await orchestrator._find_multi_artifacts("a & b")
    assert len(res_amp) == 2

def test_small_talk_greeting_thanks_vi_en(orchestrator):
    assert "Kính chào khanh" in orchestrator._build_small_talk_answer("xin chào", "vi")
    assert "Greetings, honored guest" in orchestrator._build_small_talk_answer("hello", "en")
    
    assert "rất vui khi được phụng sự" in orchestrator._build_small_talk_answer("cảm ơn", "vi")
    assert "my honor to serve you" in orchestrator._build_small_talk_answer("thank you", "en")

def test_build_general_context_includes_history(orchestrator):
    ctx = orchestrator._build_general_context("query", "History goes here", "vi")
    assert "GENERAL_CHAT" in ctx
    assert "USER_QUESTION:\nquery" in ctx
    assert "CONVERSATION_HISTORY:\nHistory goes here" in ctx

def test_resilient_fallback_differs_by_context_and_lang(orchestrator):
    msg_vi_db = orchestrator._build_resilient_fallback_answer("query", "vi", True)
    assert "tìm thấy thông tin liên quan" in msg_vi_db
    
    msg_vi_no_db = orchestrator._build_resilient_fallback_answer("query", "vi", False)
    assert "chưa có mục dữ liệu khớp" in msg_vi_no_db
    
    msg_en_db = orchestrator._build_resilient_fallback_answer("query", "en", True)
    assert "found related information" in msg_en_db
    
    msg_en_no_db = orchestrator._build_resilient_fallback_answer("query", "en", False)
    assert "do not have a matching item" in msg_en_no_db

def test_not_heard_message_vi_en(orchestrator):
    assert "chưa nghe rõ" in orchestrator._not_heard_message("vi")
    assert "did not catch that clearly" in orchestrator._not_heard_message("en")

def test_unrecognized_image_message_vi_en(orchestrator):
    assert "chưa nhận diện được" in orchestrator._unrecognized_image_message("vi")
    assert "couldn't clearly recognize" in orchestrator._unrecognized_image_message("en")

def test_has_image_observation_detects_visual_fields(orchestrator):
    class VisionRes:
        pass
    res = VisionRes()
    assert not orchestrator._has_image_observation(res)
    assert not orchestrator._has_image_observation(None)
    
    res.visual_features = "abc"
    assert orchestrator._has_image_observation(res)

def test_image_fallback_uses_visual_context_before_generic(orchestrator):
    class VisionRes:
        visual_summary = "A big gate"
        raw_label = "Unknown Gate"
    
    ans = orchestrator._build_image_fallback_answer(VisionRes(), None, "vi")
    assert "A big gate" in ans
    assert "Unknown Gate" in ans

def test_sanitize_user_response_removes_internal_prompt_labels(orchestrator):
    text = "Theo DB_CONTEXT: Ngọ Môn là cổng chính. Context Data của người dùng."
    clean = orchestrator._sanitize_user_response(text, "vi")
    assert "Theo tư liệu về di tích, Ngọ Môn là cổng chính. ngữ cảnh của người dùng." in clean

def test_format_vision_analysis_includes_candidates_and_requirement(orchestrator):
    class VisionRes:
        image_context_description = "A big gate"
        raw_label = "Ngọ Môn"
        recognition_type = "whole_building"
        top_candidates = [{"artifact_name": "Ngọ Môn", "evidence": "Looks like it", "visible_features": ["roof"]}]
        needs_user_confirmation = True
        
    analysis = orchestrator._format_vision_analysis(VisionRes(), "vi")
    assert "Ngọ Môn" in analysis
    assert "toàn cảnh" in analysis
    assert "Ứng viên gần nhất" in analysis
    assert "Yêu cầu trả lời" in analysis
    assert "thận trọng" in analysis

def test_format_artifact_context_includes_optional_fields(orchestrator):
    artifact = ArtifactInfo(
        art_id="1", loc_id="1", name_vi="Ngọ Môn", name_en="Ngo Mon", history_text_vi="Hist", history_text_en="Hist",
        visit_highlights_vi="Highlights here",
        visit_route_vi="Route here",
        nearby_context_vi="Nearby here",
        notable_objects_vi="Objects here",
        photo_spots_vi="Spots here",
    )
    ctx = orchestrator._format_artifact_context(artifact, "vi")
    assert "=== VISIBLE HIGHLIGHTS ===" in ctx
    assert "Highlights here" in ctx
    assert "=== SUGGESTED VISIT FLOW ===" in ctx
    assert "Route here" in ctx
    assert "=== NEARBY CONTEXT ===" in ctx
    assert "=== NOTABLE OBJECTS ===" in ctx
    assert "=== PHOTO SPOTS ===" in ctx

def test_artifact_name_by_lang(orchestrator):
    artifact = ArtifactInfo(art_id="1", loc_id="1", name_vi="Việt", name_en="English", history_text_vi="vi", history_text_en="en")
    assert orchestrator._artifact_name(artifact, "vi") == "Việt"
    assert orchestrator._artifact_name(artifact, "en") == "English"

def test_short_summary_truncates_cleanly(orchestrator):
    artifact = ArtifactInfo(art_id="1", loc_id="1", name_vi="A", name_en="A", history_text_en="E", history_text_vi="S1. S2. S3. S4. S5. S6. S7. S8. S9. S10. S11. S12. S13. S14. S15. S16. S17.")
    summary = orchestrator._short_summary(artifact, "vi")
    assert "S15" in summary
    assert "S16" not in summary
    
    # Also test empty history
    artifact.history_text_vi = ""
    assert orchestrator._short_summary(artifact, "vi") == ""

def test_unified_normalize_text_keeps_bracket_tokens(orchestrator):
    norm = orchestrator._normalize_text("[user sent an image] at Ngọ Môn")
    assert "[user sent an image]" in norm
    assert "ngo mon" in norm

def test_cache_key_uses_lang_artifact_query(orchestrator):
    artifact = ArtifactInfo(art_id="123", loc_id="1", name_vi="Ngọ Môn", name_en="en", history_text_vi="vi", history_text_en="en")
    key = orchestrator._cache_key(artifact, "Hỏi gì đó", "vi")
    assert key == "vi:123:hoi gi do"

def test_answer_cache_evicts_oldest_at_limit(orchestrator):
    artifact = ArtifactInfo(art_id="123", loc_id="1", name_vi="A", name_en="en", history_text_vi="vi", history_text_en="en")
    for i in range(ANSWER_CACHE_MAX_SIZE + 5):
        orchestrator._set_cached_answer(artifact, f"query {i}", "vi", f"ans {i}")
    
    assert len(_ANSWER_CACHE) == ANSWER_CACHE_MAX_SIZE
    assert orchestrator._cache_key(artifact, "query 0", "vi") not in _ANSWER_CACHE

def test_step_label_vi_en_and_unknown(orchestrator):
    assert orchestrator._step_label("stt", "vi") == "Đã chuyển giọng nói thành văn bản"
    assert orchestrator._step_label("stt", "en") == "Transcribed voice to text"
    assert orchestrator._step_label("unknown_step", "vi") == "unknown_step"

def test_make_tts_token_deterministic_and_lang_sensitive(orchestrator):
    t1 = orchestrator._make_tts_token("hello", "en")
    t2 = orchestrator._make_tts_token("hello", "en")
    t3 = orchestrator._make_tts_token("hello", "vi")
    assert t1 == t2
    assert t1 != t3
    assert len(t1) == 24

def test_build_speech_text_truncates_by_sentence(orchestrator):
    long_text = "Câu 1. Câu 2. " * 100
    speech = orchestrator._build_speech_text(long_text, "vi", max_chars=100)
    assert len(speech) <= 100
    assert "Câu 1" in speech

@pytest.mark.asyncio
async def test_background_tts_sets_ready_or_failed(orchestrator):
    tts_mock = AsyncMock()
    tts_mock.synthesize.return_value = b"audio"
    
    await orchestrator._background_tts(tts_mock, "text", "vi", "token1")
    assert _TTS_RESULT_CACHE["token1"]["status"] == "ready"
    assert _TTS_RESULT_CACHE["token1"]["audio_bytes"] == b"audio"
    
    tts_mock.synthesize.side_effect = Exception("TTS error")
    await orchestrator._background_tts(tts_mock, "text", "vi", "token2")
    assert _TTS_RESULT_CACHE["token2"]["status"] == "failed"
    assert "TTS error" in _TTS_RESULT_CACHE["token2"]["error"]

def test_fetch_tts_status_pending_ready_expired(orchestrator):
    assert UnifiedOrchestrator.fetch_tts_status("missing")["status"] == "pending"
    
    _TTS_RESULT_CACHE["tok1"] = {"status": "ready", "audio_bytes": b"x", "timestamp": time.time(), "error": None}
    assert UnifiedOrchestrator.fetch_tts_status("tok1")["status"] == "ready"
    
    _TTS_RESULT_CACHE["tok2"] = {"status": "ready", "audio_bytes": b"x", "timestamp": time.time() - _TTS_RESULT_TTL - 10, "error": None}
    assert UnifiedOrchestrator.fetch_tts_status("tok2")["status"] == "expired"
    assert "tok2" not in _TTS_RESULT_CACHE

def test_fetch_tts_audio_only_returns_when_ready(orchestrator):
    _TTS_RESULT_CACHE["tok_ready"] = {"status": "ready", "audio_bytes": b"audio_data", "timestamp": time.time(), "error": None}
    _TTS_RESULT_CACHE["tok_failed"] = {"status": "failed", "audio_bytes": None, "timestamp": time.time(), "error": "err"}
    
    assert UnifiedOrchestrator.fetch_tts_audio("tok_ready") == b"audio_data"
    assert UnifiedOrchestrator.fetch_tts_audio("tok_failed") is None

def test_evict_tts_cache_removes_expired_or_oldest(orchestrator):
    now = time.time()
    _TTS_RESULT_CACHE["expired"] = {"timestamp": now - _TTS_RESULT_TTL - 10}
    
    for i in range(_TTS_RESULT_CACHE_MAX + 5):
        _TTS_RESULT_CACHE[f"ok_{i}"] = {"timestamp": now}
        
    _evict_tts_cache()
    
    assert "expired" not in _TTS_RESULT_CACHE
    assert len(_TTS_RESULT_CACHE) <= _TTS_RESULT_CACHE_MAX
