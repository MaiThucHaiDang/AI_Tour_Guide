import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  ArrowLeft,
  Camera,
  ChevronDown,
  CheckCircle2,
  FileText,
  Image as ImageIcon,
  Landmark,
  Loader2,
  MapPin,
  Mic,
  Pause,
  Play,
  RotateCcw,
  Send,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  Upload,
  Volume2,
  VolumeX,
  X
} from 'lucide-react';
import LanguageToggle from '../shared/LanguageToggle';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import {
  unifiedChatAPI,
  playTTS,
  stopTTS,
  pauseTTS,
  resumeTTS,
  isTTSPlaying,
  isTTSPaused,
  setTTSAudioElement,
  fetchTTSAudio,
  submitFeedbackAPI,
} from '../../services/apiService';
import { compressImage } from '../../utils/imageUtils';
import CameraScanner from '../CameraScanner';

const AUDIO_HISTORY_MAX = 3;

const COPY = {
  vi: {
    title: 'AITourGuide',
    subtitle: 'Hướng dẫn viên số cho Đại Nội Huế',
    status: 'Sẵn sàng',
    back: 'Trang chủ',
    upload: 'Tải ảnh',
    camera: 'Chụp ảnh',
    askPlaceholder: 'Hỏi về Ngọ Môn, Điện Thái Hòa, Thế Miếu...',
    greeting: 'Xin chào! Bạn có thể hỏi về một điểm dừng trong Đại Nội, tải ảnh hiện vật hoặc dùng giọng nói để nghe thuyết minh.',
    processing: 'Đang chuẩn bị câu trả lời',
    artifactPanel: 'Thông tin điểm dừng',
    noArtifact: 'Chọn một marker trên bản đồ, tải ảnh hoặc đặt câu hỏi để nhận thông tin phù hợp.',
    confidence: 'Độ tin cậy',
    year: 'Năm',
    author: 'Tác giả/triều đại',
    summary: 'Tóm tắt',
    suggestions: 'Gợi ý hỏi nhanh',
    locations: 'Nhóm điểm trong Đại Nội',
    explore: 'Câu hỏi gợi ý',
    recording: 'Đang ghi âm...',
    transcribing: 'Đang chuyển giọng nói thành văn bản...',
    pendingImage: 'Ảnh chờ gửi',
    detailEmpty: 'Thông tin chi tiết sẽ xuất hiện sau khi tìm thấy điểm dừng liên quan.',
    assistantEyebrow: 'Hướng dẫn tham quan',
    reset: 'Bắt đầu lại',
    listen: 'Nghe câu trả lời',
    helpful: 'Hữu ích',
    notHelpful: 'Chưa đúng',
    feedbackThanks: 'Cảm ơn phản hồi của bạn',
    closeCamera: 'Đóng camera',
    removeImage: 'Bỏ ảnh',
    send: 'Gửi câu hỏi',
    record: 'Ghi âm',
    latest: 'Tin nhắn mới nhất',
    quickPrompts: [
      'Điện Thái Hòa được xây năm nào?',
      'Kể ngắn về Thế Miếu và Cửu Đỉnh',
      'Điện Kiến Trung có ý nghĩa gì?',
      'Duyệt Thị Đường dùng để làm gì?'
    ],
    locationsList: [
      { name: 'Cung điện & Miếu thờ', detail: 'Điện Thái Hòa, Thế Miếu, Hưng Miếu, Triệu Miếu, Thái Miếu' },
      { name: 'Cung & Vườn', detail: 'Cung Diên Thọ, Cung Trường Sanh, Vườn Cơ Hạ, Điện Kiến Trung' },
      { name: 'Cổng & Bảo tàng', detail: 'Cửa Hòa Bình, Cửa Hiển Nhơn, Cửa Chương Đức, Điện Long An' }
    ]
  },
  en: {
    title: 'AITourGuide',
    subtitle: 'A digital guide for Hue Imperial City',
    status: 'Ready',
    back: 'Home',
    upload: 'Upload',
    camera: 'Capture',
    askPlaceholder: 'Ask about Ngo Mon Gate, Thai Hoa Palace, The Mieu...',
    greeting: 'Hello! Ask about a Hue Imperial City stop, upload an artifact photo, or use voice to hear the guide.',
    processing: 'Preparing your answer',
    artifactPanel: 'Stop detail',
    noArtifact: 'Choose a map marker, upload a photo, or ask a question to get relevant guidance.',
    confidence: 'Confidence',
    year: 'Year',
    author: 'Author/dynasty',
    summary: 'Summary',
    suggestions: 'Suggested questions',
    locations: 'Citadel stop groups',
    explore: 'Suggested questions',
    recording: 'Recording...',
    transcribing: 'Transcribing voice...',
    pendingImage: 'Pending image',
    detailEmpty: 'Details will appear after a related stop is found.',
    assistantEyebrow: 'Tour guidance',
    reset: 'Start over',
    listen: 'Listen to answer',
    helpful: 'Helpful',
    notHelpful: 'Not right',
    feedbackThanks: 'Thanks for your feedback',
    closeCamera: 'Close camera',
    removeImage: 'Remove image',
    send: 'Send question',
    record: 'Record voice',
    latest: 'Latest messages',
    quickPrompts: [
      'When was Thai Hoa Palace built?',
      'Tell me about The Mieu and the Nine Dynastic Urns',
      'What is the significance of Kien Trung Palace?',
      'What was Duyet Thi Duong used for?'
    ],
    locationsList: [
      { name: 'Palaces & Temples', detail: 'Thai Hoa Palace, The Mieu, Hung Mieu, Trieu Mieu, Thai Mieu' },
      { name: 'Residences & Gardens', detail: 'Dien Tho Palace, Truong Sanh Palace, Co Ha Garden, Kien Trung Palace' },
      { name: 'Gates & Museum', detail: 'Hoa Binh Gate, Hien Nhon Gate, Chuong Duc Gate, Long An Palace' }
    ]
  }
};

const createWelcomeMessage = (greeting) => ({
  id: 'welcome',
  role: 'ai',
  type: 'text',
  content: greeting,
  timestamp: new Date(),
  source: 'template'
});

const UnifiedChatPage = ({
  onBack,
  language,
  setLanguage,
  initialArtifact,
  onArtifactUpdate,
  onProcessingStepsUpdate,
  embedded = false,
  onNarrationFinished = null
}) => {
  const copy = COPY[language] || COPY.vi;
  const [messages, setMessages] = useState(() => [createWelcomeMessage(copy.greeting)]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [inputText, setInputText] = useState('');
  const [showCamera, setShowCamera] = useState(false);
  const [pendingImage, setPendingImage] = useState(null);
  const [currentArtifact, setCurrentArtifact] = useState(null);
  const [processingSteps, setProcessingSteps] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(0);
  const [mobileGuidePanel, setMobileGuidePanel] = useState('prompts');
  const [showJumpToLatest, setShowJumpToLatest] = useState(false);
  const [playingMsgId, setPlayingMsgId] = useState(null);
  const [pausedMsgId, setPausedMsgId] = useState(null);
  const [audioHistory, setAudioHistory] = useState([]); // { id, audioBlob }

  const messagesEndRef = useRef(null);
  const messageListRef = useRef(null);
  const shouldStickToBottomRef = useRef(true);
  const sessionIdRef = useRef(null);
  const audioRef = useRef(null);
  const fileInputRef = useRef(null);
  const workspaceRef = useRef(null);
  const currentArtifactRef = useRef(null);
  const ttsCheckIntervalRef = useRef(null);

  useEffect(() => {
    currentArtifactRef.current = currentArtifact;
  }, [currentArtifact]);

  // Clean up TTS polling on unmount
  useEffect(() => {
    return () => {
      if (ttsCheckIntervalRef.current) clearTimeout(ttsCheckIntervalRef.current);
      stopTTS();
    };
  }, []);

  const {
    isRecording,
    audioBlob,
    duration,
    error: recordingError,
    startRecording,
    stopRecording,
    resetRecording,
    getFilename
  } = useAudioRecorder();

  useEffect(() => {
    onArtifactUpdate?.(currentArtifact);
  }, [currentArtifact, onArtifactUpdate]);

  useEffect(() => {
    onProcessingStepsUpdate?.(processingSteps);
  }, [onProcessingStepsUpdate, processingSteps]);



  useEffect(() => {
    if (initialArtifact) {
      const artName = language === 'vi' ? initialArtifact.name_vi : initialArtifact.name_en;
      setCurrentArtifact({
        id: initialArtifact.id,
        name: artName,
      });
      const storytellingPrompt = language === 'vi' 
        ? `Hướng dẫn viên: Giới thiệu ngắn gọn và hấp dẫn về ${artName}`
        : `Tour guide: Give a short, engaging introduction to ${artName}`;
      
      // Delay to ensure setup is done
      setTimeout(() => {
        handleSendText(storytellingPrompt, initialArtifact.id);
      }, 500);
    }
  }, [initialArtifact]);

  useEffect(() => {
    const cached = sessionStorage.getItem('unified_chat_session_id');
    if (cached) {
      sessionIdRef.current = cached;
    } else {
      const newId = `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      sessionIdRef.current = newId;
      sessionStorage.setItem('unified_chat_session_id', newId);
    }
  }, []);

  useEffect(() => {
    setMessages(prev => {
      let changed = false;
      const next = prev.map(message => {
        if (message.id !== 'welcome' || message.source !== 'template') {
          return message;
        }
        if (message.content === copy.greeting) {
          return message;
        }
        changed = true;
        return { ...message, content: copy.greeting };
      });
      return changed ? next : prev;
    });
  }, [copy.greeting]);

  useEffect(() => {
    if (!shouldStickToBottomRef.current) return;
    scrollToLatest('smooth');
  }, [messages, isProcessing]);

  useEffect(() => {
    if (audioBlob) {
      const imageToSend = pendingImage;
      setPendingImage(null);
      processUnifiedChat({
        audioBlob,
        imageBase64: imageToSend,
        filename: getFilename()
      }).finally(resetRecording);
    }
  }, [audioBlob]);

  const processUnifiedChat = async ({ text, audioBlob, imageBase64, filename, artifactId = null }) => {
    setIsProcessing(true);
    shouldStickToBottomRef.current = true;
    setShowJumpToLatest(false);
    setProcessingSteps([copy.processing]);

    let voiceMsgId = null;
    if (imageBase64) {
      setMessages(prev => [...prev, {
        id: `img-${Date.now()}`,
        role: 'user',
        type: 'image',
        content: imageBase64,
        timestamp: new Date()
      }]);
    }

    if (text) {
      setMessages(prev => [...prev, {
        id: `txt-${Date.now()}`,
        role: 'user',
        type: 'text',
        content: text,
        timestamp: new Date()
      }]);
    }

    if (audioBlob && !text) {
      voiceMsgId = `voice-${Date.now()}`;
      setMessages(prev => [...prev, {
        id: voiceMsgId,
        role: 'user',
        type: 'text',
        content: copy.transcribing,
        timestamp: new Date()
      }]);
    }

    try {
      const response = await unifiedChatAPI({
        text,
        audioBlob,
        imageBase64,
        lang: language,
        sessionId: sessionIdRef.current,
        filename,
        artifactId: artifactId || currentArtifact?.id
      });

      if (voiceMsgId && response.transcript) {
        setMessages(prev => prev.map(message => (
          message.id === voiceMsgId
            ? { ...message, content: response.transcript }
            : message
        )));
      }

      if (response.artifactId || response.artifactName) {
        setCurrentArtifact({
          id: response.artifactId,
          name: response.artifactName,
          year: response.artifactYear,
          author: response.artifactAuthor,
          summary: response.artifactSummary,
          source: response.answerSource,
        });
      }

      setProcessingSteps(response.processingSteps || []);

      const aiMsgId = `ai-${Date.now()}`;
      const aiMsg = {
        id: aiMsgId,
        role: 'ai',
        type: 'text',
        content: response.responseText || '',
        audioBlob: response.audioBlob,  // may be null (text-first)
        ttsToken: response.ttsToken,
        timestamp: new Date(),
        source: response.answerSource,
        artifactData: response.artifactId ? {
          artifact_id: response.artifactId,
          artifact_name: response.artifactName
        } : null
      };
      setIsProcessing(false);
      await appendAssistantMessageProgressively(aiMsg);

      // Poll for backend TTS audio if ttsToken is present and no inline audio
      if (response.ttsToken && (!response.audioBlob || response.audioBlob.size === 0)) {
        pollTTSAudio(response.ttsToken, aiMsgId);
      }
    } catch (error) {
      addErrorMessage(error.message);
      setProcessingSteps([]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCapture = async (photoBase64) => {
    setShowCamera(false);
    setIsProcessing(true);
    try {
      const compressed = await compressImage(photoBase64, 800, 800, 0.7);
      setPendingImage(compressed);
    } catch (err) {
      console.error('Compression error:', err);
      setPendingImage(photoBase64);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsProcessing(true);
    const reader = new FileReader();
    reader.onload = async (readerEvent) => {
      try {
        const compressed = await compressImage(readerEvent.target.result, 800, 800, 0.7);
        setPendingImage(compressed);
      } catch (err) {
        console.error('Compression error:', err);
        setPendingImage(readerEvent.target.result);
      } finally {
        setIsProcessing(false);
        event.target.value = '';
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSendText = async (overrideText = null, overrideArtifactId = null) => {
    const text = (overrideText ?? inputText).trim();
    if (!text && !pendingImage) return;
    const image = pendingImage;
    setInputText('');
    setPendingImage(null);
    await processUnifiedChat({ text, imageBase64: image, artifactId: overrideArtifactId });
  };

  const addErrorMessage = (message) => {
    shouldStickToBottomRef.current = true;
    setShowJumpToLatest(false);
    setMessages(prev => [...prev, {
      id: `err-${Date.now()}`,
      role: 'ai',
      type: 'error',
      content: getFriendlyError(message),
      timestamp: new Date(),
      source: 'error'
    }]);
  };

  const appendAssistantMessageProgressively = async (message) => {
    const fullContent = message.content || '';
    const streamId = message.id;
    const baseMessage = { ...message, content: '', isStreaming: true };
    setMessages(prev => [...prev, baseMessage]);

    if (!fullContent) {
      setMessages(prev => prev.map(item => (
        item.id === streamId ? { ...item, isStreaming: false } : item
      )));
      return;
    }

    const parts = fullContent.match(/\S+\s*/g) || [fullContent];
    let rendered = '';
    const chunkSize = fullContent.length > 500 ? 3 : 2;

    for (let index = 0; index < parts.length; index += chunkSize) {
      rendered += parts.slice(index, index + chunkSize).join('');
      setMessages(prev => prev.map(item => (
        item.id === streamId ? { ...item, content: rendered } : item
      )));
      await new Promise(resolve => setTimeout(resolve, 18));
    }

    setMessages(prev => prev.map(item => (
      item.id === streamId ? { ...item, content: fullContent, isStreaming: false } : item
    )));

    if (autoSpeak && message.audioBlob && message.audioBlob.size > 0) {
      // If inline audio is available, play it immediately
      handleSpeakMessage(message);
    } else if (!autoSpeak) {
      if (onNarrationFinished && currentArtifactRef.current) {
        onNarrationFinished(currentArtifactRef.current);
      }
    }
    // If autoSpeak but no inline audio, pollTTSAudio will handle playback
  };

  const getFriendlyError = (message = '') => {
    const lower = message.toLowerCase();
    if (lower.includes('microphone_denied')) {
      return language === 'vi'
        ? 'Trình duyệt đang chặn micro. Hãy cấp quyền micro hoặc nhập câu hỏi bằng chữ.'
        : 'Microphone access is blocked. Allow microphone permission or type your question instead.';
    }
    if (lower.includes('microphone_not_found')) {
      return language === 'vi'
        ? 'Không tìm thấy micro trên thiết bị này. Bạn vẫn có thể nhập câu hỏi bằng chữ.'
        : 'No microphone was found on this device. You can still type your question.';
    }
    if (lower.includes('recording_error')) {
      return language === 'vi'
        ? 'Không thể bắt đầu ghi âm. Hãy thử lại hoặc nhập câu hỏi bằng chữ.'
        : 'Could not start recording. Try again or type your question.';
    }
    if (lower.includes('recording_too_quiet')) {
      return language === 'vi'
        ? 'Mình chưa nghe thấy giọng nói đủ rõ. Hãy nói gần micro hơn hoặc nhập câu hỏi bằng chữ.'
        : 'I could not hear a clear voice. Speak closer to the microphone or type your question.';
    }
    if (lower.includes('camera_denied')) {
      return language === 'vi'
        ? 'Trình duyệt đang chặn camera. Hãy cấp quyền camera hoặc dùng nút tải ảnh.'
        : 'Camera access is blocked. Allow camera permission or upload a photo instead.';
    }
    if (lower.includes('camera_unsupported')) {
      return language === 'vi'
        ? 'Trình duyệt không mở được camera ở chế độ hiện tại. Hãy dùng kết nối an toàn hoặc tải ảnh lên.'
        : 'Camera access is not available in this browser mode. Use a secure connection or upload a photo.';
    }
    if (lower.includes('camera_unavailable') || lower.includes('camera_capture_failed')) {
      return language === 'vi'
        ? 'Không mở hoặc chụp được camera. Hãy thử lại hoặc tải ảnh từ máy tính.'
        : 'The camera could not be opened or captured. Try again or upload a photo.';
    }
    if (lower.includes('feedback_failed')) {
      return language === 'vi'
        ? 'Chưa lưu được phản hồi của bạn. Hãy kiểm tra backend rồi thử lại.'
        : 'Your feedback could not be saved. Check the backend, then try again.';
    }
    if (lower.includes('too large') || lower.includes('quá lớn')) {
      return language === 'vi'
        ? 'Ảnh hoặc đoạn ghi âm đang quá lớn. Hãy thử ảnh nhỏ hơn hoặc ghi âm ngắn hơn.'
        : 'The photo or recording is too large. Try a smaller photo or a shorter recording.';
    }
    if (lower.includes('timeout') || lower.includes('quá lâu')) {
      return language === 'vi'
        ? 'Xử lý quá lâu. Hãy thử lại với câu hỏi ngắn hơn, hoặc kiểm tra backend nếu lỗi tái diễn.'
        : 'Request timed out. Try a shorter question, or check the backend if this persists.';
    }
    if (lower.includes('provider') || lower.includes('api key')) {
      return language === 'vi'
        ? 'Tính năng giọng nói hoặc nhận diện hiện chưa sẵn sàng. Bạn vẫn có thể nhập câu hỏi bằng chữ.'
        : 'Voice or recognition is not ready yet. You can still type your question.';
    }
    if (lower.includes('failed to fetch') || lower.includes('network') || lower.includes('load failed')) {
      return language === 'vi'
        ? 'Chưa kết nối được backend. Hãy kiểm tra server FastAPI đang chạy rồi thử lại.'
        : 'The backend is not reachable. Check that the FastAPI server is running, then try again.';
    }
    return message || (language === 'vi'
      ? 'Mình chưa xử lý được yêu cầu này. Hãy thử hỏi ngắn hơn hoặc gửi ảnh rõ hơn.'
      : 'I could not handle this request. Try a shorter question or a clearer photo.');
  };

  useEffect(() => {
    if (!recordingError) return;
    addErrorMessage(recordingError);
    resetRecording();
  }, [recordingError, resetRecording]);

  const playAudioBlob = async (blob, msgId) => {
    stopTTS();
    if (!blob || blob.size === 0) return false;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audioRef.current = audio;
    setTTSAudioElement(audio); // register for pause/resume
    setPlayingMsgId(msgId || null);
    setPausedMsgId(null);
    try {
      await audio.play();
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setPlayingMsgId(null);
        setPausedMsgId(null);
        if (onNarrationFinished && currentArtifactRef.current) {
          onNarrationFinished(currentArtifactRef.current);
        }
      };
      return true;
    } catch (err) {
      console.error('Playback failed:', err);
      URL.revokeObjectURL(url);
      setPlayingMsgId(null);
      return false;
    }
  };

  /**
   * Poll backend for TTS audio (up to 3 times, 3s apart).
   * When audio arrives, save to audioHistory and auto-play if autoSpeak.
   */
  const pollTTSAudio = useCallback((ttsToken, msgId) => {
    let attempts = 0;
    const maxAttempts = 3;
    const poll = async () => {
      attempts++;
      const result = await fetchTTSAudio(ttsToken);
      if (result.status === 'ready' && result.audioBlob) {
        // Save to message and audio history
        setMessages(prev => prev.map(m =>
          m.id === msgId ? { ...m, audioBlob: result.audioBlob } : m
        ));
        saveToAudioHistory(msgId, result.audioBlob);
        // Auto-play if enabled
        if (autoSpeak) {
          playAudioBlob(result.audioBlob, msgId);
        }
        return;
      }
      if (attempts < maxAttempts) {
        ttsCheckIntervalRef.current = setTimeout(poll, 3000);
      } else {
        // Fallback: use Web Speech API
        if (autoSpeak) {
          const msg = messages.find(m => m.id === msgId) || {};
          if (msg.content) {
            setPlayingMsgId(msgId);
            playTTS(msg.content, language, () => {
              setPlayingMsgId(null);
              setPausedMsgId(null);
              if (onNarrationFinished && currentArtifactRef.current) {
                onNarrationFinished(currentArtifactRef.current);
              }
            });
          }
        }
      }
    };
    // Start polling after 2.5 seconds (give backend time)
    ttsCheckIntervalRef.current = setTimeout(poll, 2500);
  }, [autoSpeak, language, messages, onNarrationFinished]);

  const saveToAudioHistory = (msgId, audioBlob) => {
    setAudioHistory(prev => {
      const filtered = prev.filter(h => h.id !== msgId);
      const next = [...filtered, { id: msgId, audioBlob }];
      // Keep only AUDIO_HISTORY_MAX most recent
      return next.slice(-AUDIO_HISTORY_MAX);
    });
  };

  /**
   * Speak/Pause/Resume toggle for a message.
   */
  const handleSpeakMessage = async (message) => {
    // If this message is currently playing → pause
    if (playingMsgId === message.id && !pausedMsgId) {
      pauseTTS();
      setPlayingMsgId(null);
      setPausedMsgId(message.id);
      return;
    }
    // If this message is paused → resume
    if (pausedMsgId === message.id) {
      resumeTTS();
      setPausedMsgId(null);
      setPlayingMsgId(message.id);
      return;
    }
    // Otherwise, start playing
    // Try audioBlob first, then audioHistory, then Web Speech
    let blob = message.audioBlob;
    if (!blob || blob.size === 0) {
      const historyEntry = audioHistory.find(h => h.id === message.id);
      if (historyEntry) blob = historyEntry.audioBlob;
    }
    let played = false;
    if (blob && blob.size > 0) {
      played = await playAudioBlob(blob, message.id);
    }
    if (!played && message.content) {
      setPlayingMsgId(message.id);
      playTTS(message.content, language, () => {
        setPlayingMsgId(null);
        setPausedMsgId(null);
        if (onNarrationFinished && currentArtifactRef.current) {
          onNarrationFinished(currentArtifactRef.current);
        }
      });
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const handleResetConversation = () => {
    shouldStickToBottomRef.current = true;
    setShowJumpToLatest(false);
    stopTTS();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    const newId = `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    sessionIdRef.current = newId;
    sessionStorage.setItem('unified_chat_session_id', newId);
    setMessages([createWelcomeMessage(copy.greeting)]);
    setPendingImage(null);
    setCurrentArtifact(null);
    setProcessingSteps([]);
  };

  const scrollToLatest = (behavior = 'auto') => {
    const list = messageListRef.current;
    if (!list) return;
    list.scrollTo({
      top: list.scrollHeight,
      behavior,
    });
  };

  const handleMessageListScroll = () => {
    const list = messageListRef.current;
    if (!list) return;
    const distanceFromBottom = list.scrollHeight - list.scrollTop - list.clientHeight;
    const isNearBottom = distanceFromBottom < 96;
    shouldStickToBottomRef.current = isNearBottom;
    setShowJumpToLatest(!isNearBottom);
  };

  const handleJumpToLatest = () => {
    shouldStickToBottomRef.current = true;
    setShowJumpToLatest(false);
    scrollToLatest('smooth');
  };

  const handleFeedback = async (message, value) => {
    setMessages(prev => prev.map(item => (
      item.id === message.id ? { ...item, feedback: value } : item
    )));
    try {
      const result = await submitFeedbackAPI({
        sessionId: sessionIdRef.current,
        messageId: message.id,
        artifactId: message.artifactData?.artifact_id || null,
        rating: value === 'up' ? 'helpful' : 'not_helpful',
        answerSource: message.source || null
      });
      if (!result?.success) {
        throw new Error('feedback_failed');
      }
    } catch {
      setMessages(prev => prev.map(item => (
        item.id === message.id ? { ...item, feedback: null } : item
      )));
      addErrorMessage('feedback_failed');
    }
  };

  const handleWorkspacePointerMove = (event) => {
    const root = workspaceRef.current;
    if (!root) return;
    const x = event.clientX / window.innerWidth;
    const y = event.clientY / window.innerHeight;
    root.style.setProperty('--chat-move-x', `${(x - 0.5) * 16}px`);
    root.style.setProperty('--chat-move-y', `${(y - 0.5) * 12}px`);
  };

  const mobileGuideTabs = [
    { key: 'prompts', label: language === 'vi' ? 'Gợi ý' : 'Prompts', icon: Sparkles },
    { key: 'places', label: language === 'vi' ? 'Nhóm điểm' : 'Stops', icon: MapPin },
    { key: 'detail', label: language === 'vi' ? 'Chi tiết' : 'Detail', icon: FileText },
    { key: 'status', label: language === 'vi' ? 'Xử lý' : 'Status', icon: CheckCircle2 }
  ];

  return (
    <div className={`tour-workspace ${embedded ? 'embedded-mode' : ''}`} ref={workspaceRef} onPointerMove={handleWorkspacePointerMove}>
      <div className="chat-cursor-light" aria-hidden="true" />
      {!embedded && (
        <header className="tour-topbar">
          <button className="topbar-back" onClick={onBack} aria-label={copy.back}>
            <ArrowLeft size={18} />
            <span>{copy.back}</span>
          </button>
          <div className="brand-block">
            <div className="brand-mark"><span>AI</span></div>
            <div>
              <h1>{copy.title}</h1>
              <p>{copy.subtitle}</p>
            </div>
          </div>
          <div className="topbar-actions">
            <div className="backend-status">
              <span className="status-dot" />
              {copy.status}
            </div>
            <button
              className="topbar-icon"
              onClick={handleResetConversation}
              aria-label={copy.reset}
              title={copy.reset}
            >
              <RotateCcw size={18} />
            </button>
            <button
              className={`topbar-icon ${autoSpeak ? 'active' : ''}`}
              onClick={() => setAutoSpeak(!autoSpeak)}
              aria-label={autoSpeak ? 'Disable auto speak' : 'Enable auto speak'}
            >
              {autoSpeak ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>
            <LanguageToggle language={language} setLanguage={setLanguage} />
          </div>
        </header>
      )}

      <main className={embedded ? 'chat-only-view' : 'workspace-grid'}>
        {!embedded && (
          <aside className="explore-panel">
            <section className="panel-section">
              <div className="section-heading">
                <MapPin size={17} />
                <h2>{copy.locations}</h2>
              </div>
              <div className="location-list">
                {copy.locationsList.map((location, index) => (
                  <button
                    key={location.name}
                    className={`location-card ${selectedLocation === index ? 'selected' : ''}`}
                    onClick={() => setSelectedLocation(index)}
                  >
                    <strong>{location.name}</strong>
                    <span>{location.detail}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="panel-section">
              <div className="section-heading">
                <Sparkles size={17} />
                <h2>{copy.explore}</h2>
              </div>
              <div className="quick-actions">
                {copy.quickPrompts.map((prompt) => (
                  <button key={prompt} onClick={() => handleSendText(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </section>
          </aside>
        )}

        <section className="conversation-panel">
          <div className="conversation-header">
            <div>
              <span className="eyebrow">{copy.assistantEyebrow}</span>
              <h2>{copy.title}</h2>
            </div>
            <div className="conversation-tools">
              {embedded && (
                <>
                  <button onClick={handleResetConversation} aria-label={copy.reset} title={copy.reset}>
                    <RotateCcw size={18} />
                  </button>
                  <button
                    className={autoSpeak ? 'is-active' : ''}
                    onClick={() => setAutoSpeak(!autoSpeak)}
                    aria-label={autoSpeak
                      ? (language === 'vi' ? 'Tắt đọc tự động' : 'Disable auto speak')
                      : (language === 'vi' ? 'Bật đọc tự động' : 'Enable auto speak')}
                    title={autoSpeak
                      ? (language === 'vi' ? 'Tắt đọc tự động' : 'Disable auto speak')
                      : (language === 'vi' ? 'Bật đọc tự động' : 'Enable auto speak')}
                  >
                    {autoSpeak ? <Volume2 size={18} /> : <VolumeX size={18} />}
                  </button>
                </>
              )}
              <button onClick={() => setShowCamera(true)} aria-label={copy.camera}>
                <Camera size={18} />
                {!embedded && copy.camera}
              </button>
              <button onClick={() => fileInputRef.current?.click()} aria-label={copy.upload}>
                <Upload size={18} />
                {!embedded && copy.upload}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
            </div>
          </div>

          {embedded && (
            <section className="mobile-guide-panel" aria-label={language === 'vi' ? 'Công cụ hướng dẫn' : 'Guide tools'}>
              <div className="mobile-guide-tabs">
                {mobileGuideTabs.map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    className={mobileGuidePanel === key ? 'active' : ''}
                    onClick={() => setMobileGuidePanel(key)}
                    aria-current={mobileGuidePanel === key ? 'true' : undefined}
                  >
                    <Icon size={16} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>

              <div className="mobile-guide-content">
                {mobileGuidePanel === 'prompts' && (
                  <div className="mobile-prompt-row">
                    {copy.quickPrompts.map((prompt) => (
                      <button key={prompt} onClick={() => handleSendText(prompt)}>
                        {prompt}
                      </button>
                    ))}
                  </div>
                )}

                {mobileGuidePanel === 'places' && (
                  <div className="mobile-location-list">
                    {copy.locationsList.map((location, index) => (
                      <button
                        key={location.name}
                        className={selectedLocation === index ? 'selected' : ''}
                        onClick={() => setSelectedLocation(index)}
                      >
                        <strong>{location.name}</strong>
                        <span>{location.detail}</span>
                      </button>
                    ))}
                  </div>
                )}

                {mobileGuidePanel === 'detail' && (
                  currentArtifact ? (
                    <div className="mobile-artifact-summary">
                      <div className="artifact-mini-head">
                        <Landmark size={22} />
                        <div>
                          <span>{copy.artifactPanel}</span>
                          <strong>{currentArtifact.name || copy.artifactPanel}</strong>
                        </div>
                      </div>
                      <div className="artifact-mini-grid">
                        <div>
                          <span>{copy.year}</span>
                          <strong>{currentArtifact.year || '-'}</strong>
                        </div>
                        <div>
                          <span>{copy.author}</span>
                          <strong>{currentArtifact.author || '-'}</strong>
                        </div>
                        <div>
                          <span>ID</span>
                          <strong>{currentArtifact.id || '-'}</strong>
                        </div>
                      </div>
                      <p>{currentArtifact.summary || copy.detailEmpty}</p>
                      {currentArtifact.source && (
                        <small>{currentArtifact.source}</small>
                      )}
                    </div>
                  ) : (
                    <div className="mobile-empty-note">
                      <Landmark size={24} />
                      <p>{copy.noArtifact}</p>
                    </div>
                  )
                )}

                {mobileGuidePanel === 'status' && (
                  processingSteps.length > 0 ? (
                    <ol className="mobile-processing-steps">
                      {processingSteps.map((step, index) => (
                        <li key={`${step}-${index}`}>{step}</li>
                      ))}
                    </ol>
                  ) : (
                    <div className="mobile-empty-note">
                      <CheckCircle2 size={24} />
                      <p>{copy.detailEmpty}</p>
                    </div>
                  )
                )}
              </div>
            </section>
          )}

          <div
            ref={messageListRef}
            className="message-list"
            aria-live="polite"
            onScroll={handleMessageListScroll}
          >
            {messages.map((message) => (
              <article key={message.id} className={`message ${message.role} ${message.type}`}>
                {message.type === 'image' ? (
                  <img src={message.content} alt="Uploaded artifact" />
                ) : (
                  <>
                    <div className="message-body">
                      <p>{message.content}</p>
                      {message.isStreaming && <span className="stream-caret" aria-hidden="true" />}
                      {message.role === 'ai' && message.type !== 'error' && (
                        <button
                          className={`tts-control-btn ${playingMsgId === message.id ? 'is-playing' : ''} ${pausedMsgId === message.id ? 'is-paused' : ''}`}
                          onClick={() => handleSpeakMessage(message)}
                          aria-label={playingMsgId === message.id ? (language === 'vi' ? 'Tạm dừng' : 'Pause') : pausedMsgId === message.id ? (language === 'vi' ? 'Tiếp tục' : 'Resume') : copy.listen}
                          title={playingMsgId === message.id ? (language === 'vi' ? 'Tạm dừng' : 'Pause') : pausedMsgId === message.id ? (language === 'vi' ? 'Tiếp tục' : 'Resume') : copy.listen}
                        >
                          {playingMsgId === message.id ? <Pause size={14} /> : pausedMsgId === message.id ? <Play size={14} /> : <Volume2 size={14} />}
                        </button>
                      )}
                    </div>
                    {message.role === 'ai' && message.type !== 'error' && (
                      <div className="message-feedback">
                        {message.feedback ? (
                          <span>{copy.feedbackThanks}</span>
                        ) : (
                          <>
                            <button onClick={() => handleFeedback(message, 'up')} aria-label={copy.helpful}>
                              <ThumbsUp size={14} />
                              {copy.helpful}
                            </button>
                            <button onClick={() => handleFeedback(message, 'down')} aria-label={copy.notHelpful}>
                              <ThumbsDown size={14} />
                              {copy.notHelpful}
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </>
                )}
                <time>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
              </article>
            ))}
            {isProcessing && (
              <article className="message ai">
                <div className="message-body loading">
                  <Loader2 size={16} className="spin" />
                  <p>{copy.processing}</p>
                </div>
              </article>
            )}
            <div ref={messagesEndRef} />
          </div>

          {showJumpToLatest && (
            <button className="jump-latest" onClick={handleJumpToLatest} aria-label={copy.latest}>
              <ChevronDown size={16} />
              {copy.latest}
            </button>
          )}

          <div className="composer">
            {pendingImage && (
              <div className="pending-image">
                <img src={pendingImage} alt={copy.pendingImage} />
                <span>{copy.pendingImage}</span>
                <button onClick={() => setPendingImage(null)} aria-label={copy.removeImage}>
                  <X size={16} />
                </button>
              </div>
            )}

            {isRecording ? (
              <div className="recording-bar">
                <div className="recording-left">
                  <span className="recording-dot" />
                  <strong>{copy.recording}</strong>
                </div>
                <span className="recording-time">{formatDuration(duration)}</span>
                <button onClick={stopRecording}>
                  <Mic size={18} />
                </button>
              </div>
            ) : (
              <div className="composer-row">
                <button onClick={() => setShowCamera(true)} aria-label={copy.camera}>
                  <Camera size={20} />
                </button>
                <button onClick={() => fileInputRef.current?.click()} aria-label={copy.upload}>
                  <ImageIcon size={20} />
                </button>
                <input
                  value={inputText}
                  onChange={(event) => setInputText(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') handleSendText();
                  }}
                  placeholder={copy.askPlaceholder}
                />
                <button
                  className="send-button"
                  disabled={!inputText.trim() && !pendingImage}
                  onClick={() => handleSendText()}
                  aria-label={copy.send}
                >
                  <Send size={19} />
                </button>
                <button
                  className="mic-button"
                  onMouseDown={startRecording}
                  onTouchStart={startRecording}
                  disabled={isProcessing}
                  aria-label={copy.record}
                >
                  <Mic size={20} />
                </button>
              </div>
            )}
          </div>
        </section>

        {!embedded && (
          <aside className="artifact-panel">
            <section className="artifact-card">
              <div className="section-heading">
                <FileText size={17} />
                <h2>{copy.artifactPanel}</h2>
              </div>

              {currentArtifact ? (
                <>
                  <div className="artifact-visual">
                    <Landmark size={46} />
                  </div>
                  <h3>{currentArtifact.name || copy.artifactPanel}</h3>
                  <div className="artifact-meta-grid">
                    <div>
                      <span>{copy.year}</span>
                      <strong>{currentArtifact.year || '-'}</strong>
                    </div>
                    <div>
                      <span>{copy.author}</span>
                      <strong>{currentArtifact.author || '-'}</strong>
                    </div>
                    <div>
                      <span>ID</span>
                      <strong>{currentArtifact.id || '-'}</strong>
                    </div>
                  </div>
                  <div className="summary-block">
                    <span>{copy.summary}</span>
                    <p>{currentArtifact.summary || copy.detailEmpty}</p>
                  </div>
                </>
              ) : (
                <div className="empty-artifact">
                  <Landmark size={44} />
                  <p>{copy.noArtifact}</p>
                </div>
              )}
            </section>

            <section className="steps-card">
              <div className="section-heading">
                <CheckCircle2 size={17} />
                <h2>{language === 'vi' ? 'Trạng thái hỗ trợ' : 'Guidance status'}</h2>
              </div>
              {processingSteps.length > 0 ? (
                <ol className="processing-steps">
                  {processingSteps.map((step, index) => (
                    <li key={`${step}-${index}`}>{step}</li>
                  ))}
                </ol>
              ) : (
                <p className="muted">{copy.detailEmpty}</p>
              )}
            </section>

            <section className="panel-section suggestions-card">
              <div className="section-heading">
                <Sparkles size={17} />
                <h2>{copy.suggestions}</h2>
              </div>
              <div className="quick-actions">
                {copy.quickPrompts.slice(0, 3).map((prompt) => (
                  <button key={prompt} onClick={() => handleSendText(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </section>
          </aside>
        )}
      </main>

      {showCamera && (
        <div className="camera-overlay">
          <div className="camera-header">
            <button onClick={() => setShowCamera(false)}>
              <X size={22} />
              {copy.closeCamera}
            </button>
          </div>
          <CameraScanner
            onCapture={handleCapture}
            language={language}
            onError={addErrorMessage}
          />
        </div>
      )}

      <style>{`
        .tour-workspace {
          --ui-bg: #f4f1e8;
          --ui-paper: #fffdf6;
          --ui-surface: #ffffff;
          --ui-surface-muted: #f7faf8;
          --ui-surface-strong: #eef5f1;
          --ui-text: #182023;
          --ui-muted: #66716f;
          --ui-border: #d8d1c2;
          --ui-border-strong: #b9ad99;
          --ui-primary: #fece14;
          --ui-primary-border: #d5aa0b;
          --ui-teal: #0f5f59;
          --ui-teal-2: #1f7a72;
          --ui-red: #9d3f2f;
          --ui-blue: #315f8f;
          --ui-success: #16835e;
          --ui-danger: #b7372d;
          --ui-shadow: 0 16px 38px rgba(24, 32, 35, 0.1);
          --ui-soft-shadow: 0 8px 24px rgba(24, 32, 35, 0.07);
          height: 100dvh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          color: var(--ui-text);
          background:
            linear-gradient(90deg, rgba(24, 32, 35, 0.035) 1px, transparent 1px),
            linear-gradient(180deg, rgba(24, 32, 35, 0.025) 1px, transparent 1px),
            linear-gradient(135deg, #f7f4ea 0%, #fbfaf5 48%, #eef4f1 100%);
          background-size: 42px 42px, 42px 42px, auto;
          font-family: 'Segoe UI', 'Noto Sans', Arial, sans-serif;
        }

        /* Embedded Mode Styles */
        .tour-workspace.embedded-mode {
            background: transparent;
            border: none;
            height: 100%;
        }
        .tour-workspace.embedded-mode::before {
            display: none;
        }
        .tour-workspace.embedded-mode .chat-only-view {
            display: flex;
            flex-direction: column;
            height: 100%;
            padding: 0;
        }
        .tour-workspace.embedded-mode .conversation-panel {
            flex: 1;
            border: none;
            border-radius: 0;
            box-shadow: none;
            background: transparent;
        }
        .tour-workspace.embedded-mode .conversation-header {
            background: rgba(255, 250, 240, 0.92);
            border-bottom-color: rgba(24, 32, 35, 0.1);
        }
        .tour-workspace.embedded-mode .messages-scroll {
            background:
              linear-gradient(180deg, rgba(255, 250, 240, 0.96), rgba(246, 240, 223, 0.86));
        }
        .tour-workspace.embedded-mode .composer {
            background: rgba(255, 250, 240, 0.94);
            border-top-color: rgba(24, 32, 35, 0.12);
            backdrop-filter: blur(16px);
        }

        .tour-topbar {
          height: 74px;
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 0 clamp(14px, 2vw, 24px);
          background: rgba(255, 253, 246, 0.9);
          border-bottom: 1px solid rgba(24, 32, 35, 0.11);
          backdrop-filter: blur(18px);
          box-shadow: 0 8px 28px rgba(24, 32, 35, 0.06);
        }

        .brand-block h1,
        .conversation-header h2,
        .artifact-card h3 {
          font-family: Cambria, 'Times New Roman', serif;
          letter-spacing: 0;
        }

        .brand-mark {
          width: 42px;
          height: 42px;
          display: grid;
          place-items: center;
          border-radius: 8px;
          color: #fffdf6;
          background: var(--ui-teal);
          box-shadow: 0 10px 24px rgba(15, 95, 89, 0.24);
        }

        .brand-block {
          display: flex;
          align-items: center;
          flex: 1;
          gap: 12px;
          min-width: 240px;
        }

        .brand-block h1 {
          color: var(--ui-text);
          font-size: 23px;
          font-weight: 700;
        }

        .brand-block p {
          margin: 2px 0 0;
          color: var(--ui-muted);
          font-size: 13px;
        }

        .topbar-actions {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .topbar-back,
        .topbar-icon,
        .conversation-tools button,
        .composer-row button,
        .recording-bar button,
        .camera-header button {
          min-height: 38px;
          border: 1px solid rgba(24, 32, 35, 0.12);
          border-radius: 8px;
          color: var(--ui-text);
          background: #ffffff;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          box-shadow: 0 6px 16px rgba(24, 32, 35, 0.06);
          font-size: 13px;
          font-weight: 800;
          transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
        }

        .topbar-back:hover,
        .topbar-icon:hover,
        .conversation-tools button:hover,
        .composer-row button:hover,
        .recording-bar button:hover {
          background: var(--ui-surface-muted);
          border-color: rgba(15, 95, 89, 0.32);
          box-shadow: 0 10px 22px rgba(24, 32, 35, 0.08);
        }

        .topbar-icon {
          width: 38px;
          height: 38px;
          padding: 0;
        }

        .topbar-icon.active {
          color: #ffffff;
          background: var(--ui-teal);
          border-color: var(--ui-teal);
        }

        .backend-status {
          min-height: 38px;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          color: var(--ui-teal);
          background: rgba(15, 95, 89, 0.08);
          border: 1px solid rgba(15, 95, 89, 0.2);
          border-radius: 8px;
          padding: 8px 10px;
          font-size: 12px;
          font-weight: 800;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: var(--ui-success);
          box-shadow: 0 0 0 4px rgba(22, 131, 94, 0.14);
        }

        .tour-workspace .language-toggle {
          background: #ffffff;
          border: 1px solid rgba(24, 32, 35, 0.12);
          border-radius: 8px;
          box-shadow: 0 6px 16px rgba(24, 32, 35, 0.06);
        }

        .tour-workspace .lang-btn {
          border-radius: 6px;
          color: var(--ui-muted);
          font-weight: 900;
        }

        .tour-workspace .lang-btn.active {
          color: #ffffff;
          background: var(--ui-text);
        }

        .workspace-grid {
          flex: 1;
          min-height: 0;
          overflow: hidden;
          height: calc(100dvh - 74px);
          display: grid;
          grid-template-columns: minmax(230px, 296px) minmax(430px, 1fr) minmax(300px, 360px);
          gap: 16px;
          padding: 16px;
          background: transparent;
        }

        .explore-panel,
        .artifact-panel {
          display: flex;
          flex-direction: column;
          gap: 12px;
          min-width: 0;
          min-height: 0;
        }

        .conversation-panel {
          min-height: 0;
        }

        .panel-section,
        .artifact-card,
        .steps-card,
        .conversation-panel {
          border: 1px solid rgba(24, 32, 35, 0.12);
          border-radius: 8px;
          background: rgba(255, 253, 246, 0.88);
          box-shadow: var(--ui-soft-shadow);
        }

        .panel-section,
        .artifact-card,
        .steps-card {
          padding: 15px;
        }

        .section-heading {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-bottom: 13px;
          color: var(--ui-text);
        }

        .section-heading svg {
          width: 24px;
          height: 24px;
          padding: 4px;
          color: #fffdf6;
          background: var(--ui-red);
          border-radius: 7px;
        }

        .section-heading h2 {
          margin: 0;
          color: var(--ui-text);
          font-size: 14px;
          font-weight: 900;
          letter-spacing: 0;
        }

        .location-list,
        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: 9px;
        }

        .location-card,
        .quick-actions button {
          width: 100%;
          border: 1px solid rgba(24, 32, 35, 0.11);
          border-radius: 8px;
          color: var(--ui-text);
          background: #ffffff;
          padding: 11px;
          text-align: left;
          box-shadow: 0 4px 14px rgba(24, 32, 35, 0.04);
          transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
        }

        .location-card:hover,
        .quick-actions button:hover {
          transform: translateY(-1px);
          border-color: rgba(15, 95, 89, 0.34);
          background: #f7faf8;
          box-shadow: var(--ui-soft-shadow);
        }

        .location-card.selected {
          background: #f3fbf8;
          border-color: var(--ui-teal);
          box-shadow: inset 4px 0 0 var(--ui-teal), 0 8px 18px rgba(15, 95, 89, 0.08);
        }

        .location-card strong {
          display: block;
          color: var(--ui-text);
          font-size: 13px;
          margin-bottom: 4px;
        }

        .location-card span,
        .muted {
          color: var(--ui-muted);
          font-size: 12px;
          line-height: 1.45;
        }

        .conversation-panel {
          position: relative;
          display: flex;
          flex-direction: column;
          min-width: 0;
          overflow: hidden;
          background: var(--ui-paper);
        }

        .conversation-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 15px 16px;
          background: rgba(255, 255, 255, 0.82);
          border-bottom: 1px solid rgba(24, 32, 35, 0.1);
        }

        .conversation-header h2 {
          margin: 3px 0 0;
          color: var(--ui-text);
          font-size: 21px;
          font-weight: 700;
        }

        .eyebrow {
          color: var(--ui-teal);
          font-size: 11px;
          font-weight: 900;
          letter-spacing: 0;
          text-transform: uppercase;
        }

        .conversation-tools {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }

        .message-list {
          flex: 1;
          min-height: 0;
          overflow-y: auto;
          overscroll-behavior: contain;
          scroll-behavior: smooth;
          display: flex;
          flex-direction: column;
          padding: 18px;
          gap: 13px;
          background:
            linear-gradient(90deg, rgba(24, 32, 35, 0.026) 1px, transparent 1px),
            linear-gradient(180deg, rgba(24, 32, 35, 0.02) 1px, transparent 1px),
            #fbfaf5;
          background-size: 34px 34px;
        }

        .message-list::-webkit-scrollbar {
          width: 12px;
        }

        .message-list::-webkit-scrollbar-track {
          background: #eee9dc;
        }

        .message-list::-webkit-scrollbar-thumb {
          background: #c8bda9;
          border: 3px solid #eee9dc;
          border-radius: 999px;
        }

        .message {
          display: flex;
          flex-direction: column;
          gap: 5px;
          max-width: min(78%, 760px);
        }

        .message.ai {
          align-self: flex-start;
        }

        .message.user {
          align-self: flex-end;
        }

        .message-body {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          color: var(--ui-text);
          background: #ffffff;
          border: 1px solid rgba(24, 32, 35, 0.12);
          border-radius: 8px;
          box-shadow: var(--ui-soft-shadow);
          padding: 12px 13px;
        }

        .message.user .message-body {
          color: #ffffff;
          background: var(--ui-teal);
          border-color: var(--ui-teal);
          box-shadow: 0 12px 28px rgba(15, 95, 89, 0.16);
        }

        .message.error .message-body {
          color: #821f19;
          background: #fff3ef;
          border-color: rgba(183, 55, 45, 0.32);
        }

        .message-body p {
          margin: 0;
          font-size: 14px;
          line-height: 1.62;
          white-space: pre-wrap;
        }

        .message-body button {
          color: var(--ui-muted);
          border-radius: 6px;
        }

        .message-body button:hover {
          color: var(--ui-text);
          background: var(--ui-surface-strong);
        }

        .tts-control-btn {
          transition: color 0.2s, background 0.2s, box-shadow 0.2s;
          flex-shrink: 0;
          padding: 4px;
        }

        .tts-control-btn.is-playing {
          color: #16835e !important;
          background: #e8f5e9 !important;
          animation: tts-pulse 1.5s ease-in-out infinite;
        }

        .tts-control-btn.is-paused {
          color: #b2820a !important;
          background: #fff8e1 !important;
        }

        @keyframes tts-pulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(22, 131, 94, 0.3); }
          50% { box-shadow: 0 0 0 5px rgba(22, 131, 94, 0); }
        }

        .message.user .message-body button {
          color: #ffffff;
        }

        .stream-caret {
          display: inline-block;
          width: 7px;
          height: 1.15em;
          margin-left: 3px;
          background: var(--ui-primary);
          vertical-align: text-bottom;
          animation: blink 0.9s steps(2, start) infinite;
        }

        @keyframes blink {
          50% { opacity: 0; }
        }

        .message.image img {
          max-width: min(320px, 100%);
          border-radius: 8px;
          border: 1px solid rgba(24, 32, 35, 0.12);
          box-shadow: var(--ui-soft-shadow);
        }

        .message time {
          color: var(--ui-muted);
          font-size: 11px;
        }

        .message.user time {
          text-align: right;
        }

        .message-feedback {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 7px;
          color: var(--ui-muted);
        }

        .message-feedback button {
          border: 1px solid rgba(24, 32, 35, 0.12);
          border-radius: 8px;
          color: var(--ui-text);
          background: #ffffff;
          padding: 6px 8px;
          font-size: 12px;
          font-weight: 800;
        }

        .message-feedback button:hover {
          background: #fff8d9;
          border-color: var(--ui-primary-border);
        }

        .message-feedback span {
          color: var(--ui-success);
          font-weight: 800;
        }

        .composer {
          border-top: 1px solid rgba(24, 32, 35, 0.1);
          padding: 13px;
          background: rgba(255, 253, 246, 0.95);
          box-shadow: 0 -10px 26px rgba(24, 32, 35, 0.06);
        }

        .loading {
          align-items: center;
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .jump-latest {
          position: absolute;
          right: 16px;
          bottom: 86px;
          z-index: 3;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: #ffffff;
          background: var(--ui-red);
          border: 1px solid var(--ui-red);
          border-radius: 8px;
          padding: 8px 12px;
          font-size: 13px;
          font-weight: 800;
          box-shadow: 0 16px 30px rgba(157, 63, 47, 0.22);
        }

        .pending-image {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
          border: 1px solid rgba(15, 95, 89, 0.24);
          border-radius: 8px;
          background: #f3fbf8;
          padding: 8px;
        }

        .pending-image img {
          width: 52px;
          height: 52px;
          object-fit: cover;
          border-radius: 6px;
        }

        .pending-image span {
          flex: 1;
          font-size: 13px;
          font-weight: 800;
        }

        .pending-image button {
          width: 32px;
          height: 32px;
          margin-left: auto;
          color: var(--ui-muted);
          border-radius: 6px;
        }

        .pending-image button:hover {
          color: var(--ui-danger);
          background: #fff3ef;
        }

        .composer-row {
          display: flex;
          align-items: center;
          gap: 8px;
          min-width: 0;
        }

        .composer-row button {
          width: 42px;
          height: 42px;
          min-width: 42px;
          justify-content: center;
          padding: 0;
        }

        .composer-row input {
          min-width: 0;
          height: 42px;
          flex: 1;
          color: var(--ui-text);
          background: #ffffff;
          border: 1px solid rgba(24, 32, 35, 0.15);
          border-radius: 8px;
          padding: 0 13px;
          font-size: 14px;
          box-shadow: inset 0 1px 0 rgba(24, 32, 35, 0.04);
        }

        .composer-row input::placeholder {
          color: #8b9692;
        }

        .composer-row input:focus {
          background: #ffffff;
          border-color: var(--ui-teal);
        }

        .send-button {
          color: var(--ui-text) !important;
          background: var(--ui-primary) !important;
          border-color: var(--ui-primary-border) !important;
        }

        .send-button:disabled {
          opacity: 0.45;
          cursor: not-allowed;
          transform: none;
        }

        .composer-row .mic-button {
          width: 42px;
          height: 42px;
          min-width: 42px;
          color: #ffffff !important;
          background: var(--ui-red) !important;
          border-color: var(--ui-red) !important;
          border-radius: 8px;
          animation: none;
          box-shadow: 0 10px 22px rgba(157, 63, 47, 0.18);
          transform: none;
        }

        .composer-row .mic-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .recording-bar {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 10px;
          color: #821f19;
          background: #fff3ef;
          border: 1px solid rgba(183, 55, 45, 0.3);
          border-radius: 8px;
          padding: 9px 10px;
        }

        .recording-left {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
          min-width: 0;
          color: #821f19;
        }

        .recording-dot {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: var(--ui-danger);
          box-shadow: 0 0 0 4px rgba(183, 55, 45, 0.13);
        }

        .recording-time {
          color: var(--ui-text);
          font-variant-numeric: tabular-nums;
          font-weight: 900;
        }

        .recording-bar button {
          color: #ffffff;
          background: var(--ui-danger);
          border-color: var(--ui-danger);
        }

        .artifact-card,
        .steps-card {
          overflow: hidden;
        }

        .artifact-visual,
        .empty-artifact {
          min-height: 126px;
          border: 1px dashed rgba(15, 95, 89, 0.34);
          border-radius: 8px;
          color: var(--ui-teal);
          background:
            linear-gradient(135deg, rgba(15, 95, 89, 0.08), rgba(254, 206, 20, 0.12)),
            #f7faf8;
          text-align: center;
          padding: 18px;
        }

        .artifact-visual {
          display: grid;
          place-items: center;
        }

        .empty-artifact {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 10px;
        }

        .empty-artifact p {
          max-width: 270px;
          margin: 0;
          color: var(--ui-muted);
          line-height: 1.5;
        }

        .artifact-card h3 {
          margin: 14px 0 12px;
          color: var(--ui-text);
          font-size: 23px;
          font-weight: 700;
        }

        .artifact-meta-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
          margin-bottom: 12px;
        }

        .artifact-meta-grid div,
        .summary-block {
          border: 1px solid rgba(24, 32, 35, 0.1);
          border-radius: 8px;
          background: #ffffff;
          padding: 10px;
        }

        .artifact-meta-grid span,
        .summary-block span {
          display: block;
          margin-bottom: 5px;
          color: var(--ui-muted);
          font-size: 11px;
          font-weight: 900;
          letter-spacing: 0;
          text-transform: uppercase;
        }

        .artifact-meta-grid strong {
          color: var(--ui-text);
          font-size: 13px;
          line-height: 1.35;
        }

        .summary-block p {
          margin: 0;
          color: var(--ui-text);
          font-size: 13px;
          line-height: 1.55;
        }

        .processing-steps {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin: 0;
          padding-left: 20px;
          color: var(--ui-text);
          font-size: 13px;
          line-height: 1.45;
        }

        .processing-steps li::marker {
          color: var(--ui-red);
          font-weight: 900;
        }

        .camera-overlay {
          position: fixed;
          inset: 0;
          z-index: 100;
          display: flex;
          flex-direction: column;
          background: #050606;
        }

        .camera-header {
          display: flex;
          justify-content: flex-start;
          padding: 12px 16px;
          background: rgba(5, 6, 6, 0.86);
        }

        .camera-header button {
          color: #ffffff;
          background: rgba(255, 255, 255, 0.12);
          border-color: rgba(255, 255, 255, 0.24);
        }

        .tour-workspace button:focus-visible,
        .tour-workspace input:focus-visible {
          outline: 3px solid rgba(254, 206, 20, 0.46);
          outline-offset: 2px;
        }

        @media (max-width: 1260px) {
          .workspace-grid {
            grid-template-columns: minmax(220px, 270px) minmax(420px, 1fr);
          }

          .artifact-panel {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
        }

        @media (max-width: 920px) {
          .tour-workspace {
            overflow-y: auto;
          }

          .tour-topbar {
            height: auto;
            min-height: 74px;
            flex-wrap: wrap;
            align-items: flex-start;
            gap: 10px;
            padding: 12px 14px;
          }

          .brand-block {
            order: 1;
            flex: 1 1 250px;
            min-width: 0;
          }

          .topbar-back {
            order: 0;
          }

          .topbar-actions {
            order: 2;
            flex: 1 1 100%;
            justify-content: flex-end;
          }

          .workspace-grid {
            height: auto;
            min-height: 0;
            overflow: visible;
            grid-template-columns: 1fr;
            padding: 12px;
          }

          .explore-panel {
            display: grid;
            grid-template-columns: 1fr 1fr;
          }

          .conversation-panel {
            min-height: 640px;
          }

          .artifact-panel {
            grid-column: auto;
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 640px) {
          .tour-workspace {
            overflow-x: hidden;
          }

          .tour-topbar {
            gap: 10px;
          }

          .brand-block {
            flex-basis: 210px;
          }

          .brand-block h1 {
            font-size: 20px;
          }

          .brand-block p {
            max-width: 210px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .backend-status {
            display: none;
          }

          .topbar-actions {
            display: grid;
            grid-template-columns: 42px 42px max-content;
            justify-content: start;
            width: 100%;
          }

          .tour-workspace .language-toggle {
            margin-left: 0;
          }

          .explore-panel {
            grid-template-columns: 1fr;
          }

          .location-list,
          .quick-actions {
            flex-direction: row;
            overflow-x: auto;
            padding-bottom: 2px;
          }

          .location-card,
          .quick-actions button {
            min-width: 220px;
          }

          .conversation-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .conversation-tools {
            display: grid;
            grid-template-columns: 1fr 1fr;
            width: 100%;
          }

          .conversation-tools button {
            min-width: 0;
            justify-content: center;
            white-space: nowrap;
          }

          .message {
            max-width: 92%;
          }

          .message-list {
            padding: 14px;
          }

          .composer-row {
            flex-wrap: wrap;
          }

          .composer-row input {
            flex: 1 1 100%;
            order: -1;
          }
        }

        .tour-workspace.embedded-mode .conversation-tools {
          display: grid;
          grid-template-columns: repeat(4, 38px);
          gap: 7px;
          justify-content: end;
        }

        .tour-workspace.embedded-mode .conversation-tools button {
          width: 38px;
          min-width: 38px;
          min-height: 38px;
          justify-content: center;
          padding: 0;
        }

        .tour-workspace.embedded-mode .conversation-tools button.is-active {
          color: #fffdf6;
          background: var(--ui-teal);
          border-color: var(--ui-teal);
        }

        .mobile-guide-panel {
          flex: 0 0 auto;
          display: flex;
          flex-direction: column;
          gap: 9px;
          padding: 10px 12px 11px;
          border-bottom: 1px solid rgba(24, 32, 35, 0.1);
          background:
            linear-gradient(180deg, rgba(255, 253, 246, 0.94), rgba(247, 250, 248, 0.94));
        }

        .mobile-guide-tabs {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 6px;
        }

        .mobile-guide-tabs button {
          min-width: 0;
          min-height: 42px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 3px;
          border: 1px solid rgba(24, 32, 35, 0.11);
          border-radius: 8px;
          color: var(--ui-muted);
          background: #ffffff;
          padding: 6px 4px;
          font-size: 10.5px;
          font-weight: 900;
          line-height: 1.12;
        }

        .mobile-guide-tabs button span {
          width: 100%;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .mobile-guide-tabs button.active {
          color: #fffdf6;
          background: var(--ui-teal);
          border-color: var(--ui-teal);
          box-shadow: 0 10px 20px rgba(15, 95, 89, 0.16);
        }

        .mobile-guide-content {
          max-height: 190px;
          overflow-y: auto;
          overscroll-behavior: contain;
          padding-bottom: 1px;
        }

        .mobile-guide-content::-webkit-scrollbar,
        .mobile-prompt-row::-webkit-scrollbar {
          height: 8px;
          width: 8px;
        }

        .mobile-guide-content::-webkit-scrollbar-thumb,
        .mobile-prompt-row::-webkit-scrollbar-thumb {
          background: rgba(15, 95, 89, 0.24);
          border-radius: 999px;
        }

        .mobile-prompt-row {
          display: flex;
          gap: 8px;
          overflow-x: auto;
          padding-bottom: 2px;
        }

        .mobile-prompt-row button,
        .mobile-location-list button {
          min-height: 50px;
          border: 1px solid rgba(24, 32, 35, 0.11);
          border-radius: 8px;
          color: var(--ui-text);
          background: #ffffff;
          padding: 10px 11px;
          text-align: left;
          font-size: 12.5px;
          font-weight: 850;
          line-height: 1.32;
          box-shadow: 0 5px 14px rgba(24, 32, 35, 0.05);
        }

        .mobile-prompt-row button {
          flex: 0 0 min(260px, 82%);
        }

        .mobile-location-list {
          display: grid;
          grid-template-columns: 1fr;
          gap: 8px;
        }

        .mobile-location-list button.selected {
          border-color: var(--ui-teal);
          background: #f3fbf8;
          box-shadow: inset 4px 0 0 var(--ui-teal), 0 8px 18px rgba(15, 95, 89, 0.08);
        }

        .mobile-location-list strong {
          display: block;
          margin-bottom: 3px;
          color: var(--ui-text);
          font-size: 13px;
        }

        .mobile-location-list span {
          display: block;
          color: var(--ui-muted);
          font-size: 11.5px;
          line-height: 1.38;
        }

        .mobile-artifact-summary,
        .mobile-empty-note {
          border: 1px solid rgba(24, 32, 35, 0.11);
          border-radius: 8px;
          background: #ffffff;
          padding: 12px;
          box-shadow: 0 5px 14px rgba(24, 32, 35, 0.05);
        }

        .artifact-mini-head {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
        }

        .artifact-mini-head svg {
          flex: 0 0 auto;
          width: 38px;
          height: 38px;
          padding: 8px;
          color: #fffdf6;
          background: var(--ui-red);
          border-radius: 8px;
        }

        .artifact-mini-head span {
          display: block;
          color: var(--ui-muted);
          font-size: 10.5px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .artifact-mini-head strong {
          display: block;
          margin-top: 2px;
          color: var(--ui-text);
          font-size: 15px;
          line-height: 1.15;
        }

        .artifact-mini-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 7px;
          margin-bottom: 10px;
        }

        .artifact-mini-grid div {
          min-width: 0;
          border: 1px solid rgba(24, 32, 35, 0.09);
          border-radius: 8px;
          background: #f7faf8;
          padding: 8px;
        }

        .artifact-mini-grid span {
          display: block;
          margin-bottom: 3px;
          color: var(--ui-muted);
          font-size: 10px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .artifact-mini-grid strong {
          display: block;
          overflow-wrap: anywhere;
          color: var(--ui-text);
          font-size: 12px;
          line-height: 1.24;
        }

        .mobile-artifact-summary p,
        .mobile-empty-note p {
          margin: 0;
          color: var(--ui-text);
          font-size: 12.5px;
          line-height: 1.5;
        }

        .mobile-artifact-summary small {
          display: block;
          margin-top: 8px;
          color: var(--ui-muted);
          font-size: 11px;
          line-height: 1.35;
        }

        .mobile-empty-note {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          color: var(--ui-teal);
        }

        .mobile-empty-note svg {
          flex: 0 0 auto;
          margin-top: 2px;
        }

        .mobile-processing-steps {
          display: grid;
          gap: 8px;
          margin: 0;
          padding: 0;
          list-style: none;
        }

        .mobile-processing-steps li {
          position: relative;
          min-height: 42px;
          border: 1px solid rgba(24, 32, 35, 0.11);
          border-radius: 8px;
          background: #ffffff;
          padding: 10px 10px 10px 34px;
          color: var(--ui-text);
          font-size: 12.5px;
          line-height: 1.42;
          box-shadow: 0 5px 14px rgba(24, 32, 35, 0.05);
        }

        .mobile-processing-steps li::before {
          content: '';
          position: absolute;
          left: 12px;
          top: 14px;
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: var(--ui-teal);
          box-shadow: 0 0 0 4px rgba(15, 95, 89, 0.1);
        }

        @media (prefers-reduced-motion: reduce) {
          .tour-workspace *,
          .tour-workspace *::before,
          .tour-workspace *::after {
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.001ms !important;
          }
        }
      `}</style>
    </div>
  );
};

export default UnifiedChatPage;
