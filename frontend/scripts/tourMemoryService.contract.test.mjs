import assert from 'node:assert/strict';
import {
  createEmptyTourMemory,
  normalizeArtifactForPassport,
  loadTourMemory,
  saveTourMemory,
  clearTourMemory,
  completeTourMemory,
  recordCheckIn,
  recordPhoto,
  recordQuestion,
  recordAudio,
  buildTourSummary
} from '../src/services/tourMemoryService.js';

const makeStorage = () => {
  const storage = {};
  return {
    getItem: (key) => storage[key] || null,
    setItem: (key, val) => { storage[key] = String(val); },
    removeItem: (key) => { delete storage[key]; },
    clear: () => { Object.keys(storage).forEach((key) => delete storage[key]); }
  };
};

global.localStorage = makeStorage();
global.sessionStorage = makeStorage();

function test_empty_memory_contract() {
  const memory = createEmptyTourMemory();
  assert.equal(memory.version, 1);
  assert.equal(memory.completedAt, null);
  assert.equal(memory.totalAudioSeconds, 0);
  assert.ok(Array.isArray(memory.route));
}

function test_normalize_artifact_contract() {
  const artifact = normalizeArtifactForPassport({ artifact_id: '2', name: 'Điện Kiến Trung', lat: 16.46, lng: 107.58 });
  assert.equal(artifact.id, 2);
  assert.equal(artifact.name_vi, 'Điện Kiến Trung');
  assert.equal(artifact.lat, 16.46);
  assert.equal(normalizeArtifactForPassport({ name: 'missing id' }), null);
}

function test_save_load_clear_contract() {
  global.sessionStorage.clear();
  const memory = createEmptyTourMemory();
  memory.route.push({ artifactId: 1 });
  saveTourMemory(memory);

  const loaded = loadTourMemory();
  assert.equal(loaded.sessionId, memory.sessionId);
  assert.deepEqual(loaded.route, [{ artifactId: 1 }]);

  clearTourMemory();
  assert.equal(loadTourMemory().route.length, 0);
}

function test_checkin_completion_and_summary_contract() {
  global.sessionStorage.clear();
  const artifact = { id: '2', name_vi: 'Điện Kiến Trung', name_en: 'Kien Trung Palace' };
  let memory = loadTourMemory();

  memory = recordCheckIn(memory, artifact, { method: 'manual' });
  memory = recordCheckIn(memory, artifact, { method: 'manual' });
  assert.equal(memory.route.length, 1);
  assert.equal(memory.checkIns['2'].visits, 2);

  memory = recordPhoto(memory, {
    artifact,
    imageBase64: 'data:image/jpeg;base64,abc',
    type: 'checkin',
    source: 'photo_booth'
  });
  memory = recordQuestion(memory, { artifact, text: 'Công trình này xây năm nào?', hadImage: true });
  memory = recordAudio(memory, { artifact, seconds: 12, title: 'Giới thiệu' });
  memory = completeTourMemory(memory);

  assert.ok(memory.completedAt);
  assert.equal(memory.totalAudioSeconds, 12);

  const summary = buildTourSummary(memory, [artifact], 'vi');
  assert.equal(summary.completedCount, 1);
  assert.equal(summary.photos.length, 1);
  assert.equal(summary.checkInPhotos.length, 1);
  assert.equal(summary.questions.length, 1);
  assert.equal(summary.audio.length, 1);
}

function runTests() {
  console.log('Running tourMemoryService contract tests...');
  test_empty_memory_contract();
  test_normalize_artifact_contract();
  test_save_load_clear_contract();
  test_checkin_completion_and_summary_contract();
  console.log('tourMemoryService contract tests passed!');
}

runTests();
