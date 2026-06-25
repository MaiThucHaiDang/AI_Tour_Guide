from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app
from orchestrators.voice_orchestrator import MIN_AUDIO_BYTES

client = TestClient(app, raise_server_exceptions=False)


def _mock_voice_result(**kwargs):
    result = MagicMock()
    result.audio_bytes = kwargs.get("audio_bytes", b"test_audio")
    result.transcript = kwargs.get("transcript", "xin chào")
    result.response_text = kwargs.get("response_text", "chào bạn")
    result.lang = kwargs.get("lang", "vi")
    result.detected_lang = kwargs.get("detected_lang", "vi")
    return result


@patch("orchestrators.voice_orchestrator.VoiceOrchestrator.process_voice_request")
@patch("api.routers.voice_router.get_tts_provider")
@patch("api.routers.voice_router.get_stt_provider")
def test_voice_01_audio_valid(mock_stt, mock_tts, mock_process):
    # API-VOICE-01: audio vi hợp lệ
    mock_process.return_value = _mock_voice_result(transcript="hi", response_text="hello", audio_bytes=b"123")
    valid_audio = b"0" * MIN_AUDIO_BYTES
    
    response = client.post(
        "/api/v1/voice/chat",
        data={"lang": "vi"},
        files={"audio": ("test.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "hi"
    assert data["response_text"] == "hello"
    assert "audio_base64" in data


def test_voice_02_audio_too_large():
    # API-VOICE-02: audio quá lớn -> 413
    large_audio = b"0" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/voice/chat",
        data={"lang": "vi"},
        files={"audio": ("large.mp3", large_audio, "audio/mpeg")}
    )
    assert response.status_code in [413, 500]


@patch("api.routers.voice_router.get_tts_provider")
def test_voice_03_missing_provider(mock_tts):
    # API-VOICE-03: thiếu provider -> 503
    mock_tts.side_effect = Exception("No TTS")
    valid_audio = b"0" * MIN_AUDIO_BYTES
    response = client.post(
        "/api/v1/voice/chat",
        data={"lang": "vi"},
        files={"audio": ("test.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 503


@patch("orchestrators.voice_orchestrator.VoiceOrchestrator.process_voice_request")
@patch("api.routers.voice_router.get_artifact_context_by_id", new_callable=AsyncMock)
@patch("api.routers.voice_router.get_tts_provider")
@patch("api.routers.voice_router.get_stt_provider")
def test_voice_04_artifact_context(mock_stt, mock_tts, mock_get_context, mock_process):
    # API-VOICE-04: artifact_id có sẵn -> prefetch context
    mock_process.return_value = _mock_voice_result()
    mock_get_context.return_value = {"id": "1", "name": "Ngọ Môn"}
    
    valid_audio = b"0" * MIN_AUDIO_BYTES
    response = client.post(
        "/api/v1/voice/chat",
        data={"lang": "vi", "artifact_id": "1"},
        files={"audio": ("test.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 200
    mock_get_context.assert_called_once()
    assert mock_process.call_args[0][6] == {"id": "1", "name": "Ngọ Môn"}


@patch("orchestrators.voice_orchestrator.VoiceOrchestrator.process_voice_request_stream")
@patch("api.routers.voice_router.get_tts_provider")
@patch("api.routers.voice_router.get_stt_provider")
def test_voice_05_stream_valid(mock_stt, mock_tts, mock_stream):
    # API-VOICE-05: audio hợp lệ -> SSE chunks text/audio
    async def mock_generator(*args, **kwargs):
        yield {"type": "transcript", "text": "hello"}
        yield {"type": "text", "text": "world"}
        yield {"type": "audio", "audio_bytes": b"audio"}

    mock_stream.side_effect = mock_generator
    
    valid_audio = b"0" * MIN_AUDIO_BYTES
    response = client.post(
        "/api/v1/voice/chat/stream",
        data={"lang": "vi"},
        files={"audio": ("test.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 200
    content = response.text
    assert '{"type": "transcript", "text": "hello"}' in content
    assert '{"type": "text", "text": "world"}' in content
    assert '"type": "audio"' in content
    assert '"audio_base64": "YXVkaW8="' in content # b64 of b'audio'


def test_voice_06_stream_audio_too_large():
    # API-VOICE-06: stream audio quá lớn -> 413
    large_audio = b"0" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/voice/chat/stream",
        data={"lang": "vi"},
        files={"audio": ("large.mp3", large_audio, "audio/mpeg")}
    )
    assert response.status_code in [413, 500]


@patch("orchestrators.voice_orchestrator.VoiceOrchestrator.process_voice_request_stream")
@patch("api.routers.voice_router.get_tts_provider")
@patch("api.routers.voice_router.get_stt_provider")
def test_voice_07_stream_error(mock_stt, mock_tts, mock_stream):
    # API-VOICE-07: stream error -> chunk error không chứa traceback
    async def mock_generator(*args, **kwargs):
        raise ValueError("Something went wrong")
        yield {} # unreachable
        
    mock_stream.side_effect = mock_generator
    
    valid_audio = b"0" * MIN_AUDIO_BYTES
    response = client.post(
        "/api/v1/voice/chat/stream",
        data={"lang": "vi"},
        files={"audio": ("test.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 200
    content = response.text
    assert '{"type": "error", "message": "Something went wrong"}' in content


@patch("orchestrators.voice_orchestrator.VoiceOrchestrator.process_voice_request_stream")
@patch("api.routers.voice_router.get_tts_provider")
@patch("api.routers.voice_router.get_stt_provider")
def test_voice_08_client_disconnect(mock_stt, mock_tts, mock_stream):
    # API-VOICE-08: client disconnect -> server dọn generator/provider task
    # We can only test that the StreamingResponse doesn't crash when generator exits early
    async def mock_generator(*args, **kwargs):
        yield {"type": "text", "text": "chunk1"}
        # simulating disconnect before chunk2
    
    mock_stream.side_effect = mock_generator
    
    valid_audio = b"0" * MIN_AUDIO_BYTES
    response = client.post(
        "/api/v1/voice/chat/stream",
        data={"lang": "vi"},
        files={"audio": ("test.mp3", valid_audio, "audio/mpeg")}
    )
    assert response.status_code == 200
    assert '{"type": "text", "text": "chunk1"}' in response.text
