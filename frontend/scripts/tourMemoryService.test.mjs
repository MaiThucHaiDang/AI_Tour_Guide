import assert from 'node:assert/strict';
import {
  createEmptyTourMemory,
  normalizeArtifactForPassport,
  loadTourMemory,
  saveTourMemory,
  clearTourMemory,
  completeTourMemory,
  recordCheckIn
} from '../src/services/tourMemoryService.js';

const makeStorage = () => {
  const store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, val) => { store[key] = String(val); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach((key) => delete store[key]); }
  };
};

global.localStorage = makeStorage();
global.sessionStorage = makeStorage();

function test_create_empty_memory_has_version_session_defaults() {
  const mem = createEmptyTourMemory();
  assert.equal(mem.version, 1);
  assert.ok(mem.sessionId);
  assert.ok(Array.isArray(mem.route));
  assert.equal(mem.totalAudioSeconds, 0);
  assert.equal(mem.completedAt, null);
}

function test_normalize_artifact_accepts_api_variants() {
  const art1 = normalizeArtifactForPassport({ id: '1', name: 'Ngo Mon', lat: 16.4, lng: 107.5 });
  assert.equal(art1.id, 1);
  assert.equal(art1.name_vi, 'Ngo Mon');
  
  const art2 = normalizeArtifactForPassport({ artifact_id: '2', name: 'Thai Hoa', coordinates: { lat: 16.4, lng: 107.5 } });
  assert.equal(art2.id, 2);
}

function test_normalize_artifact_rejects_missing_id() {
  const art = normalizeArtifactForPassport({ name: 'Invalid' });
  assert.equal(art, null);
}

function test_save_and_load_memory() {
  global.sessionStorage.clear();
  const mem = createEmptyTourMemory();
  mem.route.push({ artifactId: 1 });
  saveTourMemory(mem);
  
  const loaded = loadTourMemory();
  assert.equal(loaded.sessionId, mem.sessionId);
  assert.deepEqual(loaded.route, [{ artifactId: 1 }]);
}

function test_clear_memory_removes_storage() {
  global.sessionStorage.clear();
  saveTourMemory(createEmptyTourMemory());
  clearTourMemory();
  const loaded = loadTourMemory();
  assert.equal(loaded.route.length, 0); // newly created empty
}

function test_record_checkin_first_and_repeat_visit() {
  global.sessionStorage.clear();
  let mem = loadTourMemory();
  const artifact = { id: '1', name_vi: 'Ngo Mon', lat: 16.4, lng: 107.5 };
  mem = recordCheckIn(mem, artifact);
  assert.equal(mem.route.length, 1);
  assert.equal(mem.checkIns['1'].visits, 1);
  
  // Repeat
  mem = recordCheckIn(mem, artifact);
  assert.equal(mem.route.length, 1);
  assert.equal(mem.checkIns['1'].visits, 2);
}

function test_complete_memory_sets_completed_at() {
  global.sessionStorage.clear();
  let mem = loadTourMemory();
  mem = completeTourMemory(mem);
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
