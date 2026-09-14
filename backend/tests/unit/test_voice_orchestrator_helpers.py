import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from orchestrators.voice_orchestrator import VoiceOrchestrator, VoicePipelineResult

@pytest.fixture
def stt_mock():
    m = AsyncMock()
    m.transcribe.return_value = ("xin chao", "vi")
    return m

@pytest.fixture
def llm_mock():
    m = AsyncMock()
    m.generate_response.return_value = "hello from llm"
    async def mock_stream(*args, **kwargs):
        yield "hello "
        yield "from llm"
    m.generate_response_stream = mock_stream
    return m

@pytest.fixture
def tts_mock():
    m = AsyncMock()
    m.synthesize.return_value = b"tts_audio"
    return m

@pytest.fixture
def memory_mock():
    m = AsyncMock()
    m.format_history.return_value = ""
    m.add_turn = AsyncMock()
    return m

@pytest.fixture
def orchestrator(stt_mock, llm_mock, tts_mock, memory_mock):
    db_lookup = AsyncMock(return_value="db context data")
    return VoiceOrchestrator(
        stt=stt_mock,
        llm=llm_mock,
        tts=tts_mock,
        db_lookup=db_lookup,
        memory=memory_mock
    )

@pytest.mark.asyncio
async def test_voice_process_tiny_audio_not_heard(orchestrator):
    # tiny audio
    res = await orchestrator.process_voice_request(b"tiny", "vi")
    assert res.transcript == ""
    assert res.audio_bytes == b"tts_audio"
    assert "nghe ro" in res.response_text.lower() or "not heard" in res.response_text.lower() or "chua nghe" in res.response_text.lower()
    orchestrator._stt.transcribe.assert_not_called()

@pytest.mark.asyncio
@patch("orchestrators.voice_orchestrator.graph_augmented_search", new_callable=AsyncMock)
async def test_voice_process_stt_db_llm_tts_success(mock_graph_search, orchestrator):
    mock_graph_search.return_value = []
    # 800+ bytes
    audio = b"0" * 1000
    res = await orchestrator.process_voice_request(audio, "vi", session_id="ses1")
    assert res.transcript == "xin chao"
    assert res.response_text == "hello from llm"
    assert res.audio_bytes == b"tts_audio"
    assert orchestrator._memory.add_turn.call_count == 2

@pytest.mark.asyncio
@patch("orchestrators.voice_orchestrator.graph_augmented_search", new_callable=AsyncMock)
async def test_voice_process_prefetched_context_overrides_lookup(mock_graph_search, orchestrator):
    mock_graph_search.return_value = []
    audio = b"0" * 1000
    res = await orchestrator.process_voice_request(audio, "vi", prefetched_context="prefetched")
    orchestrator._db_lookup.assert_not_called()
    mock_graph_search.assert_not_called()
    assert res.response_text == "hello from llm"

@pytest.mark.asyncio
@patch("orchestrators.voice_orchestrator.graph_augmented_search", new_callable=AsyncMock)
async def test_voice_process_no_db_context_returns_no_context_message(mock_graph_search, orchestrator):
    mock_graph_search.return_value = []
    orchestrator._db_lookup.return_value = "No matching artifact found in database."
    audio = b"0" * 1000
    res = await orchestrator.process_voice_request(audio, "vi")
    assert res.response_text == "hello from llm"
    call_args = orchestrator._llm.generate_response.call_args[0]
    assert "<NO_CONTEXT>" in call_args[1] or "GENERAL_CHAT" in call_args[1] or "CONTEXT_NOTE" in call_args[1]

@pytest.mark.asyncio
@patch("orchestrators.voice_orchestrator.graph_augmented_search", new_callable=AsyncMock)
async def test_voice_process_llm_failure_returns_fallback_audio(mock_graph_search, orchestrator):
    mock_graph_search.return_value = []
    orchestrator._llm.generate_response.side_effect = Exception("LLM Error")
    audio = b"0" * 1000
    res = await orchestrator.process_voice_request(audio, "vi")
    assert "tạm thời không sẵn sàng" in res.response_text.lower() or "temporarily unavailable" in res.response_text.lower()
    assert res.audio_bytes == b"tts_audio"

@pytest.mark.asyncio
@patch("orchestrators.voice_orchestrator.graph_augmented_search", new_callable=AsyncMock)
async def test_voice_process_tts_failure_keeps_text(mock_graph_search, orchestrator):
    mock_graph_search.return_value = []
    orchestrator._tts.synthesize.side_effect = Exception("TTS Error")
    audio = b"0" * 1000
    res = await orchestrator.process_voice_request(audio, "vi")
    assert res.response_text == "hello from llm"
    assert res.audio_bytes == b""

@pytest.mark.asyncio
@patch("orchestrators.voice_orchestrator.graph_augmented_search", new_callable=AsyncMock)
async def test_voice_stream_yields_transcript_text_audio_chunks(mock_graph_search, orchestrator):
    mock_graph_search.return_value = []
    audio = b"0" * 1000
    chunks = []
    async for chunk in orchestrator.process_voice_request_stream(audio, "vi"):
        chunks.append(chunk)
    
    types = [c["type"] for c in chunks]
    assert "transcript" in types
    assert "text" in types
    assert "audio" in types
    assert chunks[-1]["type"] == "audio"
    assert chunks[-1]["audio_bytes"] == b"tts_audio"

@pytest.mark.asyncio
@patch("orchestrators.voice_orchestrator.graph_augmented_search", new_callable=AsyncMock)
async def test_voice_stream_provider_error_yields_error_chunk_without_traceback(mock_graph_search, orchestrator):
    mock_graph_search.return_value = []
    orchestrator._stt.transcribe.side_effect = Exception("STT Error")
    audio = b"0" * 1000
    chunks = []
    async for chunk in orchestrator.process_voice_request_stream(audio, "vi"):
        chunks.append(chunk)
    
    assert len(chunks) == 1
    assert chunks[0]["type"] == "error"
    assert "STT Error" in chunks[0]["message"]
    assert "Traceback" not in chunks[0]["message"]

@pytest.mark.asyncio
async def test_call_db_lookup_accepts_sync_and_async_lookup():
    orchestrator_sync = VoiceOrchestrator(None, None, None, db_lookup=lambda x, y: "sync")
    orchestrator_async = VoiceOrchestrator(None, None, None, db_lookup=AsyncMock(return_value="async"))
    
    res1 = await orchestrator_sync._call_db_lookup("text", "field")
    res2 = await orchestrator_async._call_db_lookup("text", "field")
    
    assert res1 == "sync"
    assert res2 == "async"

def test_is_unhelpful_context_detects_no_match():
    assert VoiceOrchestrator._is_unhelpful_context(None) is True
    assert VoiceOrchestrator._is_unhelpful_context("   ") is True
    assert VoiceOrchestrator._is_unhelpful_context("No matching artifact found in database.") is True
    assert VoiceOrchestrator._is_unhelpful_context("Database is temporarily unavailable.") is True
    assert VoiceOrchestrator._is_unhelpful_context("Good data") is False

def test_voice_classify_intent_general_fact_intro():
    assert VoiceOrchestrator._classify_intent("xin chao ban") == "small_talk"
    assert VoiceOrchestrator._classify_intent("di tich nay la gi") == "artifact"
    assert VoiceOrchestrator._classify_intent("thoi tiet hom nay the nao") == "unknown"

def test_voice_normalize_text():
    assert VoiceOrchestrator._normalize_text("Đại Nội Huế") == "dai noi hue"
    assert VoiceOrchestrator._normalize_text("   Điện   Thái Hòa ") == "dien thai hoa"
    assert VoiceOrchestrator._normalize_text(None) == ""

@pytest.mark.asyncio
async def test_synthesize_response_returns_empty_on_tts_failure_or_raises_expected(orchestrator):
    orchestrator._tts.synthesize.side_effect = TimeoutError()
    res = await orchestrator._synthesize_response("text", "vi")
    assert res == b""
    
    orchestrator._tts.synthesize.side_effect = Exception("TTS Failed")
    res2 = await orchestrator._synthesize_response("text", "vi")
    assert res2 == b""
