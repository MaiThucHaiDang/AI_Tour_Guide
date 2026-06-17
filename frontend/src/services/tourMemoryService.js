const STORAGE_KEY = 'ai_tour_passport_memory_v1';
const LEGACY_STORAGE_KEY = 'ai_tour_passport_memory_v1';
const MEMORY_VERSION = 1;
const MAX_PHOTOS = 10;
const MAX_QUESTIONS = 40;
const MAX_AUDIO_ITEMS = 40;
const MAX_EVENTS = 80;

const nowIso = () => new Date().toISOString();

const createSessionId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `tour-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const safeArray = (value) => (Array.isArray(value) ? value : []);
const safeObject = (value) => (value && typeof value === 'object' && !Array.isArray(value) ? value : {});

const limitList = (items, maxItems) => safeArray(items).slice(-maxItems);

const getTourStorage = () => {
  if (typeof sessionStorage !== 'undefined') return sessionStorage;
  return null;
};

const clearLegacyPersistentMemory = () => {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem(LEGACY_STORAGE_KEY);
  }
};

const normalizeText = (value, maxLength = 400) => {
  if (!value) return '';
  const text = String(value).replace(/\s+/g, ' ').trim();
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
};

export const createEmptyTourMemory = () => ({
  version: MEMORY_VERSION,
  sessionId: createSessionId(),
  startedAt: nowIso(),
  updatedAt: nowIso(),
  completedAt: null,
  checkIns: {},
  photos: [],
  questions: [],
  audio: [],
  route: [],
  events: [],
  totalAudioSeconds: 0
});

export const normalizeArtifactForPassport = (artifact = {}) => {
  if (!artifact) return null;
  const id = artifact.id ?? artifact.artifact_id ?? artifact.artifactId ?? artifact.art_id;
  if (id === undefined || id === null || id === '') return null;

  return {
    id: Number(id),
    name_vi: artifact.name_vi || artifact.nameVi || artifact.name || artifact.artifact_name || '',
    name_en: artifact.name_en || artifact.nameEn || artifact.name || artifact.artifact_name || '',
    lat: Number.isFinite(Number(artifact.lat ?? artifact.latitude)) ? Number(artifact.lat ?? artifact.latitude) : null,
    lng: Number.isFinite(Number(artifact.lng ?? artifact.longitude)) ? Number(artifact.lng ?? artifact.longitude) : null,
    image: artifact.image || artifact.coverImage || '',
    summary: artifact.summary || artifact.artifactSummary || ''
  };
};

export const normalizeCatalogForPassport = (catalog = []) => (
  safeArray(catalog)
    .map(normalizeArtifactForPassport)
    .filter(Boolean)
    .filter((artifact, index, list) => (
      list.findIndex((item) => Number(item.id) === Number(artifact.id)) === index
    ))
);

export const loadTourMemory = () => {
  clearLegacyPersistentMemory();

  const storage = getTourStorage();
  if (!storage) return createEmptyTourMemory();

  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return createEmptyTourMemory();
    const parsed = JSON.parse(raw);
    const memory = {
      ...createEmptyTourMemory(),
      ...parsed,
      version: MEMORY_VERSION,
      checkIns: safeObject(parsed.checkIns),
      photos: safeArray(parsed.photos),
      questions: safeArray(parsed.questions),
      audio: safeArray(parsed.audio),
      route: safeArray(parsed.route),
      events: safeArray(parsed.events),
      totalAudioSeconds: Number(parsed.totalAudioSeconds || 0)
    };
    return memory.completedAt ? createEmptyTourMemory() : memory;
  } catch (error) {
    console.warn('Failed to load tour memory:', error);
    return createEmptyTourMemory();
  }
};

export const saveTourMemory = (memory) => {
  const next = {
    ...createEmptyTourMemory(),
    ...memory,
    version: MEMORY_VERSION,
    updatedAt: nowIso()
  };

  const storage = getTourStorage();
  if (storage) {
    storage.setItem(STORAGE_KEY, JSON.stringify(next));
  }
  clearLegacyPersistentMemory();
  return next;
};

export const resetTourMemory = () => {
  const next = createEmptyTourMemory();
  const storage = getTourStorage();
  if (storage) {
    storage.setItem(STORAGE_KEY, JSON.stringify(next));
  }
  clearLegacyPersistentMemory();
  return next;
};

export const clearTourMemory = () => {
  const storage = getTourStorage();
  if (storage) {
    storage.removeItem(STORAGE_KEY);
  }
  clearLegacyPersistentMemory();
  return createEmptyTourMemory();
};

export const completeTourMemory = (memory) => saveTourMemory({
  ...memory,
  completedAt: memory?.completedAt || nowIso()
});

const addEvent = (memory, event) => ({
  ...memory,
  events: limitList([
    ...safeArray(memory.events),
    {
      id: `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      createdAt: nowIso(),
      ...event
    }
  ], MAX_EVENTS)
});

export const recordCheckIn = (memory, artifactInput, details = {}) => {
  const artifact = normalizeArtifactForPassport(artifactInput);
  if (!artifact) return saveTourMemory(memory);

  const key = String(artifact.id);
  const existing = safeObject(memory.checkIns)[key] || null;
  const method = details.method || 'manual';
  const methods = Array.from(new Set([...(existing?.methods || []), method]));
  const checkedAt = nowIso();

  const nextCheckIn = {
    id: artifact.id,
    artifact,
    firstCheckedAt: existing?.firstCheckedAt || checkedAt,
    lastCheckedAt: checkedAt,
    methods,
    visits: (existing?.visits || 0) + 1,
    distanceMeters: Number.isFinite(Number(details.distanceMeters)) ? Math.round(Number(details.distanceMeters)) : existing?.distanceMeters ?? null,
    source: details.source || existing?.source || method
  };

  const route = safeArray(memory.route);
  const routeAlreadyHasStop = route.some((stop) => Number(stop.artifactId) === Number(artifact.id));
  const nextRoute = routeAlreadyHasStop
    ? route
    : [
        ...route,
        {
          artifactId: artifact.id,
          checkedAt,
          name_vi: artifact.name_vi,
          name_en: artifact.name_en,
          lat: artifact.lat,
          lng: artifact.lng,
          method
        }
      ];

  const next = addEvent({
    ...memory,
    checkIns: {
      ...safeObject(memory.checkIns),
      [key]: nextCheckIn
    },
    route: nextRoute
  }, {
    type: 'check_in',
    artifactId: artifact.id,
    method
  });

  return saveTourMemory(next);
};

export const recordPhoto = (memory, payload = {}) => {
  const artifact = normalizeArtifactForPassport(payload.artifact);
  const imageBase64 = payload.imageBase64 || payload.photoBase64 || '';
  if (!imageBase64) return saveTourMemory(memory);

  const item = {
    id: `photo-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    createdAt: nowIso(),
    artifactId: artifact?.id || null,
    artifactNameVi: artifact?.name_vi || '',
    artifactNameEn: artifact?.name_en || '',
    source: payload.source || 'camera',
    imageBase64
  };

  const next = addEvent({
    ...memory,
    photos: limitList([...safeArray(memory.photos), item], MAX_PHOTOS)
  }, {
    type: 'photo',
    artifactId: item.artifactId,
    source: item.source
  });

  return saveTourMemory(next);
};

export const recordQuestion = (memory, payload = {}) => {
  const text = normalizeText(payload.text || payload.transcript, 360);
  if (!text) return saveTourMemory(memory);
  const artifact = normalizeArtifactForPassport(payload.artifact);

  const item = {
    id: `question-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    createdAt: nowIso(),
    artifactId: artifact?.id || payload.artifactId || null,
    artifactNameVi: artifact?.name_vi || '',
    artifactNameEn: artifact?.name_en || '',
    text,
    inputType: payload.inputType || 'text',
    hadImage: Boolean(payload.hadImage)
  };

  const next = addEvent({
    ...memory,
    questions: limitList([...safeArray(memory.questions), item], MAX_QUESTIONS)
  }, {
    type: 'question',
    artifactId: item.artifactId,
    inputType: item.inputType
  });

  return saveTourMemory(next);
};

export const recordAudio = (memory, payload = {}) => {
  const artifact = normalizeArtifactForPassport(payload.artifact);
  const seconds = Math.max(0, Math.round(Number(payload.seconds || 0)));
  if (!artifact && seconds <= 0) return saveTourMemory(memory);

  const item = {
    id: `audio-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    createdAt: nowIso(),
    artifactId: artifact?.id || payload.artifactId || null,
    artifactNameVi: artifact?.name_vi || '',
    artifactNameEn: artifact?.name_en || '',
    title: normalizeText(payload.title, 160),
    seconds,
    source: payload.source || 'guide'
  };

  const next = addEvent({
    ...memory,
    totalAudioSeconds: Math.max(0, Number(memory.totalAudioSeconds || 0)) + seconds,
    audio: limitList([...safeArray(memory.audio), item], MAX_AUDIO_ITEMS)
  }, {
    type: 'audio',
    artifactId: item.artifactId,
    seconds
  });

  return saveTourMemory(next);
};

export const buildTourSummary = (memoryInput, catalogInput = [], language = 'vi') => {
  const memory = memoryInput || createEmptyTourMemory();
  const catalog = normalizeCatalogForPassport(catalogInput);
  const checkIns = safeObject(memory.checkIns);
  const route = safeArray(memory.route);
  const fallbackCatalog = route
    .filter((stop) => !catalog.some((artifact) => Number(artifact.id) === Number(stop.artifactId)))
    .map((stop) => normalizeArtifactForPassport({
      id: stop.artifactId,
      name_vi: stop.name_vi,
      name_en: stop.name_en,
      lat: stop.lat,
      lng: stop.lng
    }))
    .filter(Boolean);
  const fullCatalog = [...catalog, ...fallbackCatalog];

  const stops = fullCatalog.map((artifact) => {
    const checkIn = checkIns[String(artifact.id)] || null;
    return {
      artifact,
      checkIn,
      checked: Boolean(checkIn),
      displayName: language === 'vi'
        ? artifact.name_vi || artifact.name_en
        : artifact.name_en || artifact.name_vi
    };
  });

  const completedCount = Object.keys(checkIns).filter((id) => (
    fullCatalog.length === 0 || fullCatalog.some((artifact) => Number(artifact.id) === Number(id))
  )).length;
  const totalCount = fullCatalog.length || completedCount;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return {
    memory,
    catalog: fullCatalog,
    stops,
    checkedStops: stops.filter((stop) => stop.checked),
    routeStops: route,
    completedCount,
    totalCount,
    progressPercent,
    photos: safeArray(memory.photos),
    questions: safeArray(memory.questions),
    audio: safeArray(memory.audio),
    totalAudioSeconds: Math.max(0, Number(memory.totalAudioSeconds || 0))
  };
};
