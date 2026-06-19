// Relative paths are forwarded by Vite to the unified backend in development.
const RECOGNIZE_API_URL = '';
const VOICE_API_URL = '';

export const recognizeArtifactAPI = async (imageBase64, lang = 'vi', sessionId = null) => {
  try {
    const response = await fetch(`${RECOGNIZE_API_URL}/api/v1/recognize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image_base64: imageBase64,
        lang: lang,
        session_id: sessionId
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "NETWORK_ERROR");
    }

    if (data.success) {
      return {
        status: "success",
        data: {
          artifact_id: data.artifact_id,
          artifact_name: data.artifact_name,
          text_response: data.response_text,
          confidence_score: data.confidence_score
        }
      };
    } else {
      return {
        status: "error",
        error_code: data.error_code,
        message: data.message,
        confidence_score: data.confidence_score
      };
    }
  } catch (error) {
    console.error("Lỗi kết nối API:", error);
    throw new Error("NETWORK_ERROR");
  }
};

// Browser Text-to-Speech via Web Speech API.
let _ttsOnEndCallback = null;
let _ttsStopping = false;
let _ttsState = 'idle';
let _ttsQueue = [];
let _ttsQueueIndex = 0;
let _ttsRunId = 0;
let _ttsCurrentUtterance = null;
let _ttsCurrentChunkIndex = -1;
let _ttsPausedEndedChunkIndex = -1;
let _ttsLang = 'vi';

const TTS_MAX_CHUNK_CHARS = 220;

const getSpeechSynthesis = () => {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    return null;
  }
  return window.speechSynthesis;
};

const pickVoice = (lang) => {
  const synth = getSpeechSynthesis();
  if (!synth) return null;

  const locale = lang === 'vi' ? 'vi-VN' : 'en-US';
  const prefix = lang === 'vi' ? 'vi' : 'en';
  const voices = synth.getVoices?.() || [];
  return (
    voices.find((voice) => voice.lang === locale)
    || voices.find((voice) => voice.lang?.toLowerCase().startsWith(prefix))
    || null
  );
};

const splitTTSIntoChunks = (text, maxChars = TTS_MAX_CHUNK_CHARS) => {
  const cleaned = String(text || '').replace(/\s+/g, ' ').trim();
  if (!cleaned) return [];

  const sentences = cleaned.match(/[^.!?。！？]+[.!?。！？]*/g) || [cleaned];
  const chunks = [];
  let current = '';

  const pushLongSegment = (segment) => {
    const words = segment.split(/\s+/).filter(Boolean);
    let piece = '';
    words.forEach((word) => {
      const next = piece ? `${piece} ${word}` : word;
      if (next.length > maxChars && piece) {
        chunks.push(piece);
        piece = word;
      } else {
        piece = next;
      }
    });
    if (piece) chunks.push(piece);
  };

  sentences.forEach((sentence) => {
    const trimmed = sentence.trim();
    if (!trimmed) return;
    if (trimmed.length > maxChars) {
      if (current) {
        chunks.push(current);
        current = '';
      }
      pushLongSegment(trimmed);
      return;
    }

    const next = current ? `${current} ${trimmed}` : trimmed;
    if (next.length > maxChars && current) {
      chunks.push(current);
      current = trimmed;
    } else {
      current = next;
    }
  });

  if (current) chunks.push(current);
  return chunks;
};

const makeUtterance = (text, lang) => {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'vi' ? 'vi-VN' : 'en-US';
  utterance.rate = 1.0;
  utterance.voice = pickVoice(lang);
  return utterance;
};

const finishTTSQueue = (runId) => {
  if (runId !== _ttsRunId) return;
  _ttsCurrentUtterance = null;
  _ttsQueue = [];
  _ttsQueueIndex = 0;
  _ttsCurrentChunkIndex = -1;
  _ttsPausedEndedChunkIndex = -1;
  _ttsState = 'idle';
  const callback = _ttsOnEndCallback;
  _ttsOnEndCallback = null;
  if (!_ttsStopping && callback) callback();
};

const speakTTSChunkAt = (synth, lang, runId, chunkIndex) => {
  if (_ttsStopping || runId !== _ttsRunId) return null;
  if (chunkIndex >= _ttsQueue.length) {
    finishTTSQueue(runId);
    return null;
  }

  const utterance = makeUtterance(_ttsQueue[chunkIndex], lang);
  _ttsCurrentUtterance = utterance;
  _ttsCurrentChunkIndex = chunkIndex;
  _ttsQueueIndex = chunkIndex + 1;

  utterance.onend = () => {
    if (_ttsStopping || runId !== _ttsRunId) return;
    if (_ttsState === 'paused') {
      _ttsPausedEndedChunkIndex = chunkIndex;
      return;
    }
    speakTTSChunkAt(synth, lang, runId, chunkIndex + 1);
  };
  utterance.onerror = () => {
    if (_ttsStopping || runId !== _ttsRunId) return;
    if (_ttsState === 'paused') {
      _ttsPausedEndedChunkIndex = chunkIndex;
      return;
    }
    // Browser voices can fail on a single long sentence; continue with the remaining queue.
    speakTTSChunkAt(synth, lang, runId, chunkIndex + 1);
  };

  _ttsState = 'playing';
  synth.speak(utterance);
  return utterance;
};

const speakNextTTSChunk = (synth, lang, runId) => speakTTSChunkAt(synth, lang, runId, _ttsQueueIndex);

export const playTTS = (text, lang = 'vi', onEndCallback) => {
  stopTTS();
  _ttsStopping = false;
  _ttsOnEndCallback = onEndCallback || null;
  _ttsRunId += 1;
  _ttsLang = lang;
  _ttsPausedEndedChunkIndex = -1;

  const synth = getSpeechSynthesis();
  if (!synth) {
    console.warn("Browser does not support Web Speech API");
    _ttsState = 'idle';
    if (onEndCallback) onEndCallback();
    return null;
  }

  synth.cancel();

  _ttsQueue = splitTTSIntoChunks(text);
  _ttsQueueIndex = 0;
  if (_ttsQueue.length === 0) {
    _ttsState = 'idle';
    if (onEndCallback) onEndCallback();
    return null;
  }

  return speakNextTTSChunk(synth, lang, _ttsRunId);
};

export const stopTTS = () => {
  _ttsStopping = true;
  _ttsOnEndCallback = null;
  _ttsState = 'idle';
  _ttsQueue = [];
  _ttsQueueIndex = 0;
  _ttsCurrentUtterance = null;
  _ttsCurrentChunkIndex = -1;
  _ttsPausedEndedChunkIndex = -1;
  _ttsRunId += 1;

  const synth = getSpeechSynthesis();
  if (synth) {
    synth.cancel();
  }

  setTimeout(() => {
    _ttsStopping = false;
  }, 0);
};

export const pauseTTS = () => {
  const synth = getSpeechSynthesis();
  if (!synth || _ttsCurrentChunkIndex < 0 || _ttsQueue.length === 0 || _ttsState !== 'playing') return false;
  synth.pause();
  _ttsState = 'paused';
  return true;
};

export const resumeTTS = () => {
  const synth = getSpeechSynthesis();
  if (!synth || (!synth.paused && _ttsState !== 'paused')) return false;
  if (_ttsPausedEndedChunkIndex >= 0) {
    const nextChunkIndex = _ttsPausedEndedChunkIndex + 1;
    _ttsPausedEndedChunkIndex = -1;
    if (synth.paused) {
      synth.resume();
    }
    if (nextChunkIndex >= _ttsQueue.length) {
      finishTTSQueue(_ttsRunId);
      return true;
    }
    speakTTSChunkAt(synth, _ttsLang, _ttsRunId, nextChunkIndex);
  } else if (synth.paused && synth.speaking) {
    synth.resume();
  } else if (!synth.speaking && _ttsCurrentChunkIndex >= 0 && _ttsQueue[_ttsCurrentChunkIndex]) {
    speakTTSChunkAt(synth, _ttsLang, _ttsRunId, _ttsCurrentChunkIndex);
  } else if (synth.paused) {
    synth.resume();
  }
  _ttsState = 'playing';
  return true;
};

export const isTTSPlaying = () => {
  const synth = getSpeechSynthesis();
  return Boolean((synth && synth.speaking && !synth.paused) || _ttsState === 'playing');
};

export const getTTSQueueInfo = () => ({
  total: _ttsQueue.length,
  current: _ttsQueueIndex,
  state: _ttsState,
  currentChunk: _ttsCurrentChunkIndex,
  pausedEndedChunk: _ttsPausedEndedChunkIndex,
  currentText: _ttsCurrentUtterance?.text || '',
});

export const isTTSPaused = () => {
  const synth = getSpeechSynthesis();
  return Boolean((synth && synth.paused) || _ttsState === 'paused');
};

export const getTTSState = () => {
  const synth = getSpeechSynthesis();
  if (!synth) return 'unsupported';
  if (synth.paused || _ttsState === 'paused') return 'paused';
  if ((synth.speaking && !synth.paused) || _ttsState === 'playing') return 'playing';
  return 'idle';
};

/**
 * Poll the backend for TTS audio by token.
 * Returns { status: "ready", audioBlob } or { status: "pending" }.
 */
export const fetchTTSAudio = async (ttsToken) => {
  if (!ttsToken) return { status: 'none' };

  try {
    const response = await fetch(`/api/v1/tts/fetch?tts_token=${encodeURIComponent(ttsToken)}`);
    if (!response.ok) return { status: 'error' };
    const data = await response.json();
    if (data.status === 'ready' && data.audio_base64) {
      const blob = base64ToBlob(data.audio_base64, data.audio_mime || 'audio/mpeg');
      return { status: 'ready', audioBlob: blob };
    }
    if (data.status === 'failed' || data.status === 'expired') {
      return { status: data.status, message: data.message || data.status };
    }
    return { status: 'pending' };
  } catch (err) {
    console.warn('fetchTTSAudio error:', err);
    return { status: 'error' };
  }
};


/**
 * Gửi ghi âm lên API Voice Chat
 */
const USE_MOCK = false;

export const voiceChatAPI = async (
  audioBlob,
  lang = 'vi',
  signal = null,
  filename = 'recording.webm',
  sessionId = null,
  artifactId = null,
  artifactName = null
) => {
  if (USE_MOCK) {
    console.warn("[MOCK] Sending audio blob:", audioBlob.size, "bytes", "Language:", lang);
    return new Promise((resolve, reject) => {
      const controller = new AbortController();
      if (signal) {
        signal.addEventListener('abort', () => controller.abort());
      }

      const timeoutId = setTimeout(() => {
        if (controller.signal.aborted) {
          clearTimeout(timeoutId);
          reject(new Error('TIMEOUT'));
          return;
        }

        const text = lang === 'vi' 
          ? 'Đây là kết quả giả lập từ Frontend. Ngọ Môn được xây dựng năm 1833 dưới triều vua Minh Mạng.'
          : 'This is a mock result from Frontend. Ngo Mon Gate was built in 1833 during Emperor Minh Mang reign.';
        const transcript = lang === 'vi'
          ? 'Toi muon biet ve Ngo Mon.'
          : 'Tell me about Ngo Mon Gate.';
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang === 'vi' ? 'vi-VN' : 'en-US';
        window.speechSynthesis.speak(utterance);

        const mockBlob = new Blob(['mock audio data'], { type: 'audio/mpeg' });
        clearTimeout(timeoutId);
        resolve({ audioBlob: mockBlob, transcript, responseText: text });
      }, 2000); // Giả lập độ trễ 2 giây của mạng
    });
  }
  const formData = new FormData();
  formData.append('audio', audioBlob, filename);
  formData.append('lang', lang);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  if (artifactId) {
    formData.append('artifact_id', artifactId);
  }
  if (artifactName) {
    formData.append('artifact_name', artifactName);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);

  if (signal) {
    signal.addEventListener('abort', () => controller.abort());
  }

  try {
    const response = await fetch(`${VOICE_API_URL}/api/v1/chat/unified`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const data = await response.json();
      return {
        audioBlob: data.audio_base64 ? base64ToBlob(data.audio_base64, data.audio_mime || 'audio/mpeg') : null,
        transcript: data.transcript || '',
        responseText: data.response_text || '',
        speechText: data.speech_text || data.response_text || '',
      };
    }

    return {
      audioBlob: await response.blob(),
      transcript: '',
      responseText: '',
    };
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('TIMEOUT');
    }
    throw error;
  }
};

/**
 * Unified Chat API: Gửi Text, Audio, và Image cùng lúc (Multimodal)
 */
export const unifiedChatAPI = async ({
  text = null,
  audioBlob = null,
  imageBase64 = null,
  lang = 'vi',
  sessionId = null,
  artifactId = null,
  filename = 'recording.webm'
}) => {
  const formData = new FormData();
  if (text) formData.append('text', text);
  if (imageBase64) formData.append('image_base64', imageBase64);
  if (audioBlob) formData.append('audio', audioBlob, filename);
  formData.append('lang', lang);
  if (sessionId) formData.append('session_id', sessionId);
  if (artifactId) formData.append('artifact_id', artifactId);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);

  try {
    const response = await fetch(`${VOICE_API_URL}/api/v1/chat/unified`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    let audioBlobResult = null;
    if (data.audio_base64) {
      audioBlobResult = base64ToBlob(data.audio_base64, data.audio_mime || 'audio/mpeg');
    }

    return {
      success: data.success,
      responseText: data.response_text,
      speechText: data.speech_text || data.response_text || '',
      audioBlob: audioBlobResult,
      transcript: data.transcript,
      artifactId: data.artifact_id,
      artifactName: data.artifact_name,
      artifactYear: data.artifact_year,
      artifactAuthor: data.artifact_author,
      artifactSummary: data.artifact_summary,
      answerSource: data.answer_source,
      processingSteps: data.processing_steps || [],
      ttsToken: data.tts_token || null,
    };
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Yêu cầu quá lâu. Backend xử lý chậm hoặc AI đang quá tải, hãy thử lại.');
    }
    console.error("Unified Chat Error:", error);
    throw error;
  }
};

export const submitFeedbackAPI = async ({
  sessionId = null,
  messageId = null,
  artifactId = null,
  rating,
  comment = null,
  intent = null,
  answerSource = null
}) => {
  if (!rating) return { success: false };
  const response = await fetch('/api/v1/feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: sessionId,
      message_id: messageId,
      artifact_id: artifactId,
      rating,
      comment,
      intent,
      answer_source: answerSource
    })
  });

  if (!response.ok) {
    return { success: false };
  }
  return response.json();
};

const base64ToBlob = (base64, mimeType = 'audio/mpeg') => {
  if (!base64) {
    return new Blob([], { type: mimeType });
  }
  const byteString = atob(base64);
  const len = byteString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) {
    bytes[i] = byteString.charCodeAt(i);
  }
  return new Blob([bytes], { type: mimeType });
};

export const getMapConfigAPI = async () => {
  try {
    const response = await fetch('/api/v1/map/config');
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Failed to fetch map configuration');
    }
    return data;
  } catch (error) {
    console.error('Error fetching map configuration:', error);
    throw error;
  }
};

export const getRouteAPI = async ({ start, end, lang = 'vi' }) => {
  const params = new URLSearchParams({
    start_lat: start.lat,
    start_lng: start.lng,
    end_lat: end.lat,
    end_lng: end.lng,
    lang
  });

  try {
    const response = await fetch(`/api/v1/map/route?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Failed to calculate route');
    }
    return data;
  } catch (error) {
    console.error('Error calculating route:', error);
    throw error;
  }
};

export const saveMapConfigAPI = async (mapBounds, artifacts) => {
  try {
    const response = await fetch('/api/v1/map/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        map_bounds: mapBounds,
        artifacts: artifacts.map(art => ({
          id: art.id,
          lat: art.lat,
          lng: art.lng
        }))
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Failed to save map configuration');
    }
    return data;
  } catch (error) {
    console.error('Error saving map configuration:', error);
    throw error;
  }
};

export const planTourAPI = async ({ start, maxDuration = 60, maxPlaces = 5, lang = 'vi' }) => {
  const params = new URLSearchParams({
    start_lat: start.lat,
    start_lng: start.lng,
    max_duration: maxDuration,
    max_places: maxPlaces,
    lang
  });

  try {
    const response = await fetch(`/api/v1/map/plan-tour?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Failed to plan tour');
    }
    return data;
  } catch (error) {
    console.error('Error planning tour:', error);
    throw error;
  }
};

export const getNextSuggestionAPI = async ({ currentArtifactId, visitedIds = [], lang = 'vi' }) => {
  const params = new URLSearchParams({
    current_artifact_id: currentArtifactId,
    visited_ids: visitedIds.join(','),
    lang
  });

  try {
    const response = await fetch(`/api/v1/map/next-suggestion?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Failed to get next suggestions');
    }
    return data;
  } catch (error) {
    console.error('Error getting next suggestions:', error);
    throw error;
  }
};

export const createGameRoomAPI = async (visitedIds, lang = 'vi', hostNickname = '') => {
  try {
    const response = await fetch('/api/v1/game/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        visited_ids: visitedIds,
        lang,
        host_nickname: hostNickname || undefined
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to create game room');
    return data;
  } catch (error) {
    console.error('Error creating game room:', error);
    throw error;
  }
};

export const joinGameRoomAPI = async (roomCode, nickname) => {
  try {
    const response = await fetch('/api/v1/game/join', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        room_code: roomCode,
        nickname
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to join game room');
    return data;
  } catch (error) {
    console.error('Error joining game room:', error);
    throw error;
  }
};

export const startGameAPI = async (roomCode) => {
  try {
    const response = await fetch('/api/v1/game/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        room_code: roomCode
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to start game');
    return data;
  } catch (error) {
    console.error('Error starting game:', error);
    throw error;
  }
};

export const submitAnswerAPI = async (roomCode, nickname, questionIndex, selectedOption) => {
  try {
    const response = await fetch('/api/v1/game/answer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        room_code: roomCode,
        nickname,
        question_index: questionIndex,
        selected_option: selectedOption
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to submit answer');
    return data;
  } catch (error) {
    console.error('Error submitting answer:', error);
    throw error;
  }
};

export const nextQuestionAPI = async (roomCode) => {
  try {
    const response = await fetch('/api/v1/game/next', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        room_code: roomCode
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to advance game');
    return data;
  } catch (error) {
    console.error('Error advancing game:', error);
    throw error;
  }
};

export const endGameAPI = async (roomCode) => {
  try {
    const response = await fetch('/api/v1/game/end', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        room_code: roomCode
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to end game');
    return data;
  } catch (error) {
    console.error('Error ending game:', error);
    throw error;
  }
};

export const getGameRoomStatusAPI = async (roomCode) => {
  try {
    const response = await fetch(`/api/v1/game/room/${roomCode}/status`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get room status');
    return data;
  } catch (error) {
    console.error('Error getting room status:', error);
    throw error;
  }
};

export const getGameRoomPraiseAPI = async (roomCode) => {
  try {
    const response = await fetch(`/api/v1/game/room/${roomCode}/praise`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get AI praise');
    return data;
  } catch (error) {
    console.error('Error getting AI praise:', error);
    throw error;
  }
};

export const getLocalIpAPI = async () => {
  try {
    const response = await fetch('/api/v1/game/local-ip');
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get local IP');
    return data;
  } catch (error) {
    console.error('Error getting local IP:', error);
    throw error;
  }
};

export const BLOG_TAGS = [
  'Kinh nghiệm',
  'Lịch trình',
  'Văn hóa - lịch sử',
  'Ẩm thực',
  'Review',
  'Mẹo du lịch'
];

const normalizeBlogComment = (comment = {}) => ({
  id: comment.id ?? comment.comment_id,
  postId: comment.post_id,
  authorName: comment.author_name || 'Khách',
  content: comment.content || '',
  createdAt: comment.created_at
});

const normalizeBlogPost = (post = {}) => ({
  id: post.id ?? post.post_id,
  slug: post.slug,
  title: post.title || '',
  excerpt: post.excerpt || '',
  content: post.content || '',
  coverImage: post.cover_image || '/assets/images/art_17_1.jpg',
  coverAlt: post.cover_alt || 'Ảnh bìa mặc định bài viết du lịch Huế',
  authorName: post.author_name || 'AITourGuide',
  sourceType: post.source_type || 'user',
  sourceName: post.source_name || '',
  sourceUrl: post.source_url || '',
  tags: Array.isArray(post.tags) ? post.tags : [],
  createdAt: post.created_at,
  updatedAt: post.updated_at,
  publishedAt: post.published_at || post.created_at,
  readingTime: post.reading_time || 1,
  likesCount: post.likes_count || 0,
  commentsCount: post.comments_count || 0,
  bookmarksCount: post.bookmarks_count || 0,
  status: post.status || 'published',
  comments: Array.isArray(post.comments) ? post.comments.map(normalizeBlogComment) : []
});

const parseBlogResponse = async (response) => {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || `HTTP ${response.status}`);
  }
  return data;
};

export const getBlogPostsAPI = async ({ search = '', tag = '', limit = 30, offset = 0 } = {}) => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });
  if (search.trim()) params.set('search', search.trim());
  if (tag.trim()) params.set('tag', tag.trim());

  const response = await fetch(`/api/v1/blog-posts?${params.toString()}`);
  const data = await parseBlogResponse(response);
  return {
    success: data.success,
    total: data.total || 0,
    posts: Array.isArray(data.posts) ? data.posts.map(normalizeBlogPost) : []
  };
};

export const getBlogPostAPI = async (slug) => {
  const response = await fetch(`/api/v1/blog-posts/${encodeURIComponent(slug)}`);
  const data = await parseBlogResponse(response);
  return normalizeBlogPost(data.post);
};

export const createBlogPostAPI = async (payload) => {
  const response = await fetch('/api/v1/blog-posts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: payload.title,
      excerpt: payload.excerpt,
      content: payload.content,
      cover_image: payload.coverImage,
      cover_alt: payload.coverAlt,
      author_name: payload.authorName,
      tags: payload.tags,
      status: payload.status || 'published'
    })
  });
  const data = await parseBlogResponse(response);
  return normalizeBlogPost(data.post);
};

export const addBlogCommentAPI = async (slug, payload) => {
  const response = await fetch(`/api/v1/blog-posts/${encodeURIComponent(slug)}/comments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      author_name: payload.authorName || 'Khách',
      content: payload.content
    })
  });
  const data = await parseBlogResponse(response);
  return normalizeBlogComment(data);
};

export const updateBlogInteractionAPI = async (slug, payload) => {
  const response = await fetch(`/api/v1/blog-posts/${encodeURIComponent(slug)}/interactions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: payload.action,
      active: payload.active
    })
  });
  return parseBlogResponse(response);
};

