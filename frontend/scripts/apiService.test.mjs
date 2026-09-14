import assert from 'node:assert/strict';
import {
  recognizeArtifactAPI,
  voiceChatAPI,
  unifiedChatAPI,
  submitFeedbackAPI,
  getMapConfigAPI,
  getRouteAPI,
  saveMapConfigAPI,
  planTourAPI,
  getNextSuggestionAPI,
  createGameRoomAPI,
  joinGameRoomAPI,
  startGameAPI,
  submitAnswerAPI,
  nextGameQuestionAPI,
  endGameAPI,
  getGameStatusAPI,
  generateAIPraiseAPI,
  getLocalIpAPI,
  fetchBlogPostsAPI,
  fetchBlogPostDetailAPI,
  createBlogPostAPI,
  createBlogCommentAPI,
  recordBlogInteractionAPI
} from '../src/services/apiService.js';

// Setup global fetch mock
global.fetch = async (url, options) => {
  if (url.includes('/api/v1/recognize')) {
    if (options.body.get('image')?.size > 1000) {
      return { ok: false, status: 413, json: async () => ({ message: 'Image too large' }) };
    }
    return { ok: true, json: async () => ({ success: true, data: { artifact_id: '1' } }) };
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
    return { ok: true, json: async () => ({ success: true, text: 'Hello' }) };
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

global.File = class File {
  constructor(bits, name, options) {
    this.size = bits[0]?.length || 0;
    this.name = name;
  }
};

async function test_recognize_api_success_maps_backend_fields() {
  const file = new global.File(['tiny'], 'test.jpg', { type: 'image/jpeg' });
  const result = await recognizeArtifactAPI(file, { lat: 16.4, lng: 107.5 });
  assert.equal(result.status, 'success');
  assert.equal(result.data.artifact_id, '1');
}

async function test_recognize_api_backend_error_returns_status_error() {
  const origFetch = global.fetch;
  global.fetch = async () => ({ ok: true, json: async () => ({ success: false, message: 'Recognize failed' }) });
  try {
    const file = new global.File(['tiny'], 'test.jpg', { type: 'image/jpeg' });
    const result = await recognizeArtifactAPI(file, {});
    assert.equal(result.status, 'error');
    assert.equal(result.error, 'Recognize failed');
  } finally {
    global.fetch = origFetch;
  }
}

async function test_voice_chat_api_builds_formdata_and_abort_signal() {
  const file = new global.File(['tiny'], 'test.webm', { type: 'audio/webm' });
  const result = await voiceChatAPI(file, 'vi', 'sess', { lat: 16.4, lng: 107.5 }, '123', null);
  assert.equal(result.success, true);
}

async function test_unified_chat_api_builds_text_image_audio_formdata() {
  const result = await unifiedChatAPI('Hello', null, null, 'vi', 'sess', null);
  assert.equal(result.success, true);
}

async function test_submit_feedback_api_payload_shape() {
  const result = await submitFeedbackAPI('sess', '123', true, 'Good');
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
