import assert from 'node:assert/strict';
import { PHOTO_BOOTH_FRAMES } from '../src/data/photoBoothFrames.js';

const createQuotaStorage = (quotaBytes = Number.POSITIVE_INFINITY) => {
  const data = new Map();
  return {
    getItem(key) {
      return data.has(key) ? data.get(key) : null;
    },
    setItem(key, value) {
      const next = new Map(data);
      next.set(key, String(value));
      const usedBytes = Array.from(next.values()).reduce((total, item) => total + item.length, 0);
      if (usedBytes > quotaBytes) {
        const error = new Error('Quota exceeded');
        error.name = 'QuotaExceededError';
        throw error;
      }
      data.set(key, String(value));
    },
    removeItem(key) {
      data.delete(key);
    }
  };
};

globalThis.localStorage = createQuotaStorage();
globalThis.sessionStorage = createQuotaStorage(900_000);

const {
  buildTourSummary,
  createEmptyTourMemory,
  recordCheckIn,
  recordPhoto
} = await import('../src/services/tourMemoryService.js');

const artifactIds = [17, 2, 8, 12];
const artifacts = artifactIds.map((id) => {
  const frame = PHOTO_BOOTH_FRAMES[id];
  assert.ok(frame, `Missing photo booth frame for artifact ${id}`);
  return {
    id,
    name_vi: frame.nameVi,
    name_en: frame.nameEn,
    lat: 16 + id / 100,
    lng: 107 + id / 100
  };
});

const fakeAlbumImage = (index) => (
  `data:image/jpeg;base64,${'A'.repeat(105_000 + index * 1000)}`
);

let memory = createEmptyTourMemory();

artifacts.forEach((artifact, index) => {
  const frame = PHOTO_BOOTH_FRAMES[artifact.id];
  memory = recordPhoto(memory, {
    artifact,
    imageBase64: fakeAlbumImage(index),
    type: 'checkin',
    source: 'photo_booth',
    frameKey: frame.key
  });
  memory = recordCheckIn(memory, artifact, {
    method: 'photo_booth',
    source: 'photo_booth'
  });
});

memory = recordPhoto(memory, {
  artifact: artifacts[0],
  imageBase64: 'data:image/jpeg;base64,SCAN_UPLOAD_SHOULD_NOT_EXPORT',
  type: 'scan',
  source: 'scan_match'
});

const summary = buildTourSummary(memory, artifacts, 'vi');
assert.equal(summary.photos.length, 5, 'Tour memory should keep scan photos separately from album check-ins');
assert.equal(summary.checkInPhotos.length, 4, 'Album should keep 4 check-in photos');
assert.equal(summary.checkedStops.length, 4, 'Tour memory should keep 4 checked stops');
assert.deepEqual(
  summary.checkInPhotos.map((photo) => photo.artifactId).sort((a, b) => a - b),
  artifactIds.slice().sort((a, b) => a - b),
  'Album photos should belong to the tested stops'
);
assert.ok(summary.checkInPhotos.every((photo) => photo.imageBase64.startsWith('data:image/jpeg;base64,')));
assert.equal(
  summary.checkInPhotos.some((photo) => photo.imageBase64.includes('SCAN_UPLOAD_SHOULD_NOT_EXPORT')),
  false,
  'Uploaded chat/scan images must not appear in the check-in album'
);

globalThis.sessionStorage = createQuotaStorage(1);
assert.doesNotThrow(() => {
  recordPhoto(memory, {
    artifact: artifacts[0],
    imageBase64: fakeAlbumImage(9),
    type: 'checkin',
    source: 'photo_booth',
    frameKey: PHOTO_BOOTH_FRAMES[artifacts[0].id].key
  });
}, 'Storage quota failures must not crash the app');

console.log('Photo booth album test passed for 4 stops: Ngo Mon, Kien Trung, Thai Hoa, Co Ha.');
