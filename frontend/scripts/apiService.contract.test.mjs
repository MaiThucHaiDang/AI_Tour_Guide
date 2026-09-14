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
  nextQuestionAPI,
  endGameAPI,
  getGameRoomStatusAPI,
  getGameRoomPraiseAPI,
  getLocalIpAPI,
  getBlogPostsAPI,
  getBlogPostAPI,
  createBlogPostAPI,
  addBlogCommentAPI,
  updateBlogInteractionAPI
} from '../src/services/apiService.js';

const calls = [];

const jsonResponse = (body, { ok = true, status = 200, headers = {} } = {}) => ({
  ok,
  status,
  headers: {
    get: (name) => headers[name.toLowerCase()] || headers[name] || 'application/json'
  },
  json: async () => body,
  blob: async () => new Blob(['audio'], { type: 'audio/mpeg' })
});

global.fetch = async (url, options = {}) => {
  calls.push({ url: String(url), options });

  if (url === '/api/v1/recognize') {
    return jsonResponse({
      success: true,
      artifact_id: 'kien-trung',
      artifact_name: 'Dien Kien Trung',
      response_text: 'Recognized.',
      confidence_score: 0.93
    });
  }

  if (url === '/api/v1/chat/unified') {
    return jsonResponse({
      success: true,
      response_text: 'Hello',
      speech_text: 'Hello',
      transcript: 'Xin chao',
      artifact_id: '1',
      artifact_name: 'Ngo Mon',
      answer_source: 'template',
      processing_steps: ['text'],
      tts_token: 'tts-1'
    });
  }

  if (url === '/api/v1/feedback') return jsonResponse({ success: true });
  if (url === '/api/v1/map/config') {
    if (options.method === 'POST') return jsonResponse({ success: true });
    return jsonResponse({ success: true, artifacts: [{ id: '1', lat: 16.46, lng: 107.58 }] });
  }
  if (String(url).startsWith('/api/v1/map/route')) return jsonResponse({ success: true, route: [] });
  if (String(url).startsWith('/api/v1/map/plan-tour')) return jsonResponse({ success: true, route: [] });
  if (String(url).startsWith('/api/v1/map/next-suggestion')) return jsonResponse({ success: true, suggestions: [] });
  if (url === '/api/v1/game/create') return jsonResponse({ success: true, room_code: 'ABCD' });
  if (url === '/api/v1/game/join') return jsonResponse({ success: true });
  if (url === '/api/v1/game/start') return jsonResponse({ success: true, status: 'playing' });
  if (url === '/api/v1/game/answer') return jsonResponse({ success: true, correct: true });
  if (url === '/api/v1/game/next') return jsonResponse({ success: true });
  if (url === '/api/v1/game/end') return jsonResponse({ success: true, status: 'finished' });
  if (String(url).endsWith('/status')) return jsonResponse({ success: true, status: 'playing' });
  if (String(url).endsWith('/praise')) return jsonResponse({ success: true, praise: 'Good.' });
  if (url === '/api/v1/game/local-ip') return jsonResponse({ success: true, ip: '127.0.0.1' });
  if (String(url).startsWith('/api/v1/blog-posts/demo/comments')) {
    return jsonResponse({ comment_id: 9, post_id: 1, author_name: 'Khach', content: 'Hay' });
  }
  if (String(url).startsWith('/api/v1/blog-posts/demo/interactions')) return jsonResponse({ success: true });
  if (url === '/api/v1/blog-posts') {
    return jsonResponse({ success: true, post: { post_id: 2, slug: 'new-post', title: 'Bai viet moi' } });
  }
  if (String(url).startsWith('/api/v1/blog-posts/demo')) {
    return jsonResponse({
      success: true,
      post: {
        post_id: 1,
        slug: 'demo',
        title: 'Demo',
        comments: [{ comment_id: 1, author_name: 'A', content: 'B' }]
      }
    });
  }
  if (String(url).startsWith('/api/v1/blog-posts?')) {
    return jsonResponse({ success: true, total: 1, posts: [{ post_id: 1, slug: 'demo', title: 'Demo' }] });
  }
  return jsonResponse({ message: 'Not found' }, { ok: false, status: 404 });
};

function resetCalls() {
  calls.length = 0;
}

function lastCall() {
  return calls.at(-1);
}

async function test_recognize_contract() {
  resetCalls();
  const result = await recognizeArtifactAPI('data:image/jpeg;base64,abc', 'vi', 'sess');
  assert.equal(result.status, 'success');
  assert.equal(result.data.artifact_id, 'kien-trung');
  assert.equal(JSON.parse(lastCall().options.body).session_id, 'sess');
}

async function test_voice_and_unified_chat_contracts() {
  resetCalls();
  const voiceResult = await voiceChatAPI(new Blob(['tiny']), 'vi', null, 'recording.webm', 'sess', '1', 'Ngo Mon');
  assert.equal(voiceResult.responseText, 'Hello');
  assert.equal(lastCall().options.body.get('artifact_name'), 'Ngo Mon');

  const chatResult = await unifiedChatAPI({ text: 'Hello', imageBase64: 'abc', lang: 'en', sessionId: 'sess' });
  assert.equal(chatResult.ttsToken, 'tts-1');
  assert.equal(lastCall().options.body.get('image_base64'), 'abc');
}

async function test_feedback_map_game_blog_contracts() {
  resetCalls();
  assert.equal((await submitFeedbackAPI({ rating: 'helpful', sessionId: 'sess' })).success, true);
  assert.equal((await getMapConfigAPI()).success, true);
  await saveMapConfigAPI([[0, 0], [1, 1]], [{ id: '1', lat: 16.46, lng: 107.58 }]);
  await getRouteAPI({ start: { lat: 1, lng: 2 }, end: { lat: 3, lng: 4 } });
  await planTourAPI({ start: { lat: 1, lng: 2 } });
  await getNextSuggestionAPI({ currentArtifactId: '1', visitedIds: ['1', '2'] });

  assert.equal((await createGameRoomAPI(['1'], 'vi', 'Host')).room_code, 'ABCD');
  await joinGameRoomAPI('ABCD', 'Guest');
  await startGameAPI('ABCD');
  await submitAnswerAPI('ABCD', 'Guest', 0, 1);
  await nextQuestionAPI('ABCD');
  await endGameAPI('ABCD');
  await getGameRoomStatusAPI('ABCD');
  await getGameRoomPraiseAPI('ABCD');
  assert.equal((await getLocalIpAPI()).ip, '127.0.0.1');

  assert.equal((await getBlogPostsAPI({ search: 'ngo mon' })).posts[0].id, 1);
  assert.equal((await getBlogPostAPI('demo')).comments[0].id, 1);
  assert.equal((await createBlogPostAPI({ title: 'T', excerpt: 'E', content: 'C' })).slug, 'new-post');
  assert.equal((await addBlogCommentAPI('demo', { content: 'Hay' })).id, 9);
  assert.equal((await updateBlogInteractionAPI('demo', { action: 'like', active: true })).success, true);
}

async function runTests() {
  console.log('Running apiService contract tests...');
  await test_recognize_contract();
  await test_voice_and_unified_chat_contracts();
  await test_feedback_map_game_blog_contracts();
  console.log('apiService contract tests passed!');
}

runTests().catch((error) => {
  console.error(error);
  process.exit(1);
});
