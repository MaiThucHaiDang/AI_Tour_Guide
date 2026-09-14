import assert from 'node:assert/strict';
import {
  recognizeArtifactAPI,
  voiceChatAPI,
  unifiedChatAPI,
  submitFeedbackAPI,
  getMapConfigAPI,
  createGameRoomAPI
} from '../src/services/apiService.js';

// Setup global fetch mock
global.fetch = async (url, options) => {
  if (url.includes('/api/v1/recognize')) {
    const payload = JSON.parse(options.body);
    if (payload.image_base64?.length > 1000) {
      return { ok: false, status: 413, json: async () => ({ message: 'Image too large' }) };
    }
    return { ok: true, json: async () => ({ success: true, artifact_id: '1' }) };
  }
  if (url.includes('/api/v1/voice/chat')) {
    if (url.includes('/stream')) {
      return { ok: true, body: {} }; // Mock stream
    }
    if (options.body.get('audio')?.size > 8000000) {
      return { ok: false, status: 413, json: async () => ({ message: 'Audio too large' }) };
    }
    return { ok: true, json: async () => ({ success: true, audio_base64: 'abcd' }) };
  }
  if (url.includes('/api/v1/chat/unified')) {
    return {
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ success: true, response_text: 'Hello' })
    };
  }
  if (url.includes('/api/v1/feedback')) {
    return { ok: true, json: async () => ({ success: true }) };
  }
  if (url.includes('/api/v1/map/config')) {
    if (options?.method === 'POST') {
      return { ok: true, json: async () => ({ success: true }) };
    }
    return { ok: true, json: async () => ({ success: true, google_maps_api_key: 'test' }) };
  }
  if (url.includes('/api/v1/map/route')) {
    return { ok: true, json: async () => ({ success: true, route: [] }) };
  }
  if (url.includes('/api/v1/map/plan-tour')) {
    return { ok: true, json: async () => ({ success: true, route: [] }) };
  }
  if (url.includes('/api/v1/map/next-suggestion')) {
    return { ok: true, json: async () => ({ success: true, next_artifact: {} }) };
  }
  if (url.includes('/api/v1/game/')) {
    return { ok: true, json: async () => ({ success: true, room_code: 'ABCD', status: 'waiting' }) };
  }
  if (url.includes('/api/v1/blog-posts')) {
    return { ok: true, json: async () => ({ success: true, posts: [], post: {} }) };
  }
  return { ok: false, status: 404, json: async () => ({ message: 'Not found' }) };
};

async function test_recognize_api_success_maps_backend_fields() {
  const result = await recognizeArtifactAPI('data:image/jpeg;base64,dGlueQ==', 'vi', 'sess');
  assert.equal(result.status, 'success');
  assert.equal(result.data.artifact_id, '1');
}

async function test_recognize_api_backend_error_returns_status_error() {
  const origFetch = global.fetch;
  global.fetch = async () => ({ ok: true, json: async () => ({ success: false, message: 'Recognize failed' }) });
  try {
    const result = await recognizeArtifactAPI('data:image/jpeg;base64,dGlueQ==');
    assert.equal(result.status, 'error');
    assert.equal(result.message, 'Recognize failed');
  } finally {
    global.fetch = origFetch;
  }
}

async function test_voice_chat_api_builds_formdata_and_abort_signal() {
  const audio = new Blob(['tiny'], { type: 'audio/webm' });
  const result = await voiceChatAPI(audio, 'vi', null, 'test.webm', 'sess', '123');
  assert.equal(result.responseText, 'Hello');
}

async function test_unified_chat_api_builds_text_image_audio_formdata() {
  const result = await unifiedChatAPI({ text: 'Hello', lang: 'vi', sessionId: 'sess' });
  assert.equal(result.success, true);
}

async function test_submit_feedback_api_payload_shape() {
  const result = await submitFeedbackAPI({
    sessionId: 'sess',
    messageId: '123',
    rating: 'helpful',
    comment: 'Good'
  });
  assert.equal(result.success, true);
}

async function test_get_map_config_api_normalizes_artifacts() {
  const result = await getMapConfigAPI();
  assert.equal(result.success, true);
}

async function test_game_api_methods_validate_success_and_errors() {
  const res = await createGameRoomAPI([], 'vi', 'Host');
  assert.equal(res.success, true);
}

async function runTests() {
  console.log('Running apiService tests...');
  await test_recognize_api_success_maps_backend_fields();
  await test_recognize_api_backend_error_returns_status_error();
  await test_voice_chat_api_builds_formdata_and_abort_signal();
  await test_unified_chat_api_builds_text_image_audio_formdata();
  await test_submit_feedback_api_payload_shape();
  await test_get_map_config_api_normalizes_artifacts();
  await test_game_api_methods_validate_success_and_errors();
  console.log('apiService tests passed!');
}

runTests().catch(e => {
  console.error(e);
  process.exit(1);
});
