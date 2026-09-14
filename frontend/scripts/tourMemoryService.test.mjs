import assert from 'node:assert/strict';
import {
  createEmptyTourMemory,
  normalizeArtifactForPassport,
  normalizeCatalogForPassport,
  loadTourMemory,
  saveTourMemory,
  resetTourMemory,
  clearTourMemory,
  completeTourMemory,
  recordCheckIn,
  recordPhoto,
  recordQuestion,
  recordAudio,
  buildTourSummary
} from '../src/services/tourMemoryService.js';

// Mock localStorage
const store = {};
global.localStorage = {
  getItem: (key) => store[key] || null,
  setItem: (key, val) => { store[key] = String(val); },
  removeItem: (key) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach(k => delete store[k]); }
};

function test_create_empty_memory_has_version_session_defaults() {
  const mem = createEmptyTourMemory();
  assert.equal(mem.version, '1.1');
  assert.ok(mem.sessionId);
  assert.ok(Array.isArray(mem.route));
  assert.equal(mem.totalAudioSeconds, 0);
  assert.equal(mem.status, 'active');
}

function test_normalize_artifact_accepts_api_variants() {
  const art1 = normalizeArtifactForPassport({ id: '1', name: 'Ngo Mon', lat: 16.4, lng: 107.5 });
  assert.equal(art1.id, '1');
  assert.equal(art1.name, 'Ngo Mon');
  
  const art2 = normalizeArtifactForPassport({ artifact_id: '2', name: 'Thai Hoa', coordinates: { lat: 16.4, lng: 107.5 } });
  assert.equal(art2.id, '2');
}

function test_normalize_artifact_rejects_missing_id() {
  const art = normalizeArtifactForPassport({ name: 'Invalid' });
  assert.equal(art, null);
}

function test_save_and_load_memory() {
  global.localStorage.clear();
  const mem = createEmptyTourMemory();
  mem.route.push('1');
  saveTourMemory(mem);
  
  const loaded = loadTourMemory();
  assert.equal(loaded.sessionId, mem.sessionId);
  assert.deepEqual(loaded.route, ['1']);
}

function test_clear_memory_removes_storage() {
  global.localStorage.clear();
  saveTourMemory(createEmptyTourMemory());
  clearTourMemory();
  const loaded = loadTourMemory();
  assert.equal(loaded.route.length, 0); // newly created empty
}

function test_record_checkin_first_and_repeat_visit() {
  global.localStorage.clear();
  let mem = loadTourMemory();
  mem = recordCheckIn(mem, { id: '1', name: 'Ngo Mon', lat: 16.4, lng: 107.5 });
  assert.deepEqual(mem.route, ['1']);
  assert.equal(mem.visitedCatalogs['1'].visits, 1);
  
  // Repeat
  mem = recordCheckIn(mem, { id: '1', name: 'Ngo Mon', lat: 16.4, lng: 107.5 });
  assert.deepEqual(mem.route, ['1']); // Not duplicated in route
  assert.equal(mem.visitedCatalogs['1'].visits, 2);
}

function test_complete_memory_sets_completed_at() {
  global.localStorage.clear();
  let mem = loadTourMemory();
  mem = completeTourMemory(mem);
  assert.equal(mem.status, 'completed');
  assert.ok(mem.completedAt);
}

function runTests() {
  console.log('Running tourMemoryService tests...');
  test_create_empty_memory_has_version_session_defaults();
  test_normalize_artifact_accepts_api_variants();
  test_normalize_artifact_rejects_missing_id();
  test_save_and_load_memory();
  test_clear_memory_removes_storage();
  test_record_checkin_first_and_repeat_visit();
  test_complete_memory_sets_completed_at();
  console.log('tourMemoryService tests passed!');
}

runTests();
