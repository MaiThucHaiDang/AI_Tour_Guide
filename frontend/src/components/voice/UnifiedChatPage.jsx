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
  Navigation,
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
import ImageGallery from '../shared/ImageGallery';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import {
  unifiedChatAPI,
  playTTS,
  stopTTS,
  pauseTTS,
  resumeTTS,
  submitFeedbackAPI,
} from '../../services/apiService';
import { compressImage } from '../../utils/imageUtils';
import CameraScanner from '../CameraScanner';

const COPY = {
  vi: {
    title: 'Hướng dẫn Đại Nội',
    subtitle: 'Hướng dẫn viên số cho Đại Nội Huế',
    status: 'Sẵn sàng',
    back: 'Trang chủ',
    upload: 'Tải ảnh',
    camera: 'Chụp ảnh',
    askPlaceholder: 'Hỏi về Ngọ Môn, Điện Thái Hòa, Thế Miếu...',
    greeting: 'Xin chào! Bạn có thể chọn một điểm trên bản đồ, tải ảnh hiện vật hoặc dùng giọng nói để nghe thuyết minh.',
    processing: 'Đang chuẩn bị câu trả lời',
    artifactPanel: 'Thông tin điểm dừng',
    noArtifact: 'Chọn một điểm trên bản đồ, tải ảnh hoặc đặt câu hỏi để nhận thông tin phù hợp.',
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
    contextEyebrow: 'Đang hỏi về',
    listenIntro: 'Nghe giới thiệu',
    nextStopQuestion: 'Đi tiếp đâu?',
    findingNextStop: 'Đang tìm điểm phù hợp tiếp theo...',
    nextStopTitle: 'Điểm tiếp theo',
    showRoute: 'Xem đường đi',
    previewNext: 'Nghe trước',
    noNextStop: 'Chưa tìm thấy điểm tiếp theo phù hợp. Bạn có thể chọn một điểm khác trên bản đồ.',
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
    title: 'Citadel Guide',
    subtitle: 'A digital guide for Hue Imperial City',
    status: 'Ready',
    back: 'Home',
    upload: 'Upload',
    camera: 'Capture',
    askPlaceholder: 'Ask about Ngo Mon Gate, Thai Hoa Palace, The Mieu...',
    greeting: 'Hello! Choose a stop on the map, upload an artifact photo, or use voice to hear the guide.',
    processing: 'Preparing your answer',
    artifactPanel: 'Stop detail',
    noArtifact: 'Choose a stop on the map, upload a photo, or ask a question to get relevant guidance.',
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
    contextEyebrow: 'Asking about',
    listenIntro: 'Hear intro',
    nextStopQuestion: 'Where next?',
    findingNextStop: 'Finding a good next stop...',
    nextStopTitle: 'Next stop',
    showRoute: 'Show route',
    previewNext: 'Preview',
    noNextStop: 'No suitable next stop was found yet. You can choose another stop on the map.',
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

const getArtifactDisplayName = (artifact, language) => {
  if (!artifact) return '';
  return artifact.name
    || (language === 'vi' ? artifact.name_vi || artifact.nameVi : artifact.name_en || artifact.nameEn)
    || artifact.artifact_name
    || artifact.name_vi
    || artifact.name_en
    || artifact.nameVi
    || artifact.nameEn
    || '';
};

const toChatArtifact = (artifact, language) => ({
  id: artifact?.id || artifact?.artifact_id || artifact?.artifactId || null,
  name: getArtifactDisplayName(artifact, language),
  year: artifact?.year || artifact?.artifactYear || null,
  author: artifact?.author || artifact?.artifactAuthor || null,
  summary: artifact?.summary || artifact?.artifactSummary || artifact?.summary_vi || artifact?.summary_en || '',
  source: artifact?.source || artifact?.answerSource || '',
  openHoursVi: artifact?.openHoursVi || '',
  openHoursEn: artifact?.openHoursEn || '',
  ticketVi: artifact?.ticketVi || '',
  ticketEn: artifact?.ticketEn || '',
  highlightVi: artifact?.highlightVi || '',
  highlightEn: artifact?.highlightEn || '',
  images: artifact?.images || []
});

const getContextPrompts = (artifactName, language) => {
  if (!artifactName) return [];
  return language === 'vi'
    ? [
        `Nghe giới thiệu ngắn về ${artifactName}`,
        `${artifactName} có gì đặc biệt?`,
        `Tôi nên quan sát gì ở ${artifactName}?`,
        `Đi tiếp đâu sau ${artifactName}?`
      ]
    : [
        `Give me a short intro to ${artifactName}`,
        `What is special about ${artifactName}?`,
        `What should I notice at ${artifactName}?`,
        `Where should I go after ${artifactName}?`
      ];
};

const getSuggestionName = (suggestion, language) => (
  language === 'vi'
    ? suggestion?.name_vi || suggestion?.name || suggestion?.name_en || ''
    : suggestion?.name_en || suggestion?.name || suggestion?.name_vi || ''
);

const UnifiedChatPage = ({
  onBack,
  language,
  setLanguage,
  initialArtifact,
  onArtifactUpdate,
  onProcessingStepsUpdate,
  embedded = false,
  onNarrationFinished = null,
  nextSuggestion = null,
  onRequestNextStop = null,
  onNavigateNextStop = null,
  onPreviewNextStop = null,
  onPassportCheckIn = null,
  onPassportPhoto = null,
  onPassportQuestion = null,
  onPassportAudio = null
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

  const [activeAudioMsgId, setActiveAudioMsgId] = useState(null);
  const [speechState, setSpeechState] = useState('idle');

  const messagesEndRef = useRef(null);
  const messageListRef = useRef(null);
  const shouldStickToBottomRef = useRef(true);
  const sessionIdRef = useRef(null);
  const fileInputRef = useRef(null);
  const workspaceRef = useRef(null);
  const currentArtifactRef = useRef(null);
  const messagesRef = useRef(messages);
  const lastInitialArtifactKeyRef = useRef(null);

  useEffect(() => {
    currentArtifactRef.current = currentArtifact;
  }, [currentArtifact]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const estimateSpeechSeconds = useCallback((text = '') => {
    const words = String(text).trim().split(/\s+/).filter(Boolean).length;
    if (!words) return 0;
    return Math.max(6, Math.round(words / 2.4));
  }, []);

  useEffect(() => {
    return () => {
      stopTTS();
    };
  }, []);

  const {
    isRecording,
    audioBlob,
    duration: recordDuration,
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
      const artifactForChat = toChatArtifact(initialArtifact, language);
      const artifactKey = [
        artifactForChat.id || artifactForChat.name,
        initialArtifact.selectedAt || '',
        initialArtifact.entryAction || 'intro'
      ].join(':');

      if (lastInitialArtifactKeyRef.current === artifactKey) return;
      lastInitialArtifactKeyRef.current = artifactKey;

      setCurrentArtifact(artifactForChat);
      setMobileGuidePanel('detail');

      if (initialArtifact.entryAction === 'context') {
        shouldStickToBottomRef.current = true;
        setMessages(prev => [...prev, {
          id: `ctx-${Date.now()}`,
          role: 'ai',
          type: 'text',
          content: language === 'vi'
            ? `Mình đang theo điểm ${artifactForChat.name}. Bạn muốn nghe giới thiệu, hỏi thêm, hay xem điểm kế tiếp?`
            : `I am following ${artifactForChat.name}. Would you like an intro, a deeper question, or the next stop?`,
          timestamp: new Date(),
          source: 'template'
        }]);
        return;
      }

      const storytellingPrompt = language === 'vi'
        ? `Nghe giới thiệu ngắn về ${artifactForChat.name}`
        : `Give me a short introduction to ${artifactForChat.name}`;

      window.setTimeout(() => {
        handleSendText(storytellingPrompt, artifactForChat.id);
      }, 300);
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
    handleStopAudio();
    setIsProcessing(true);
    shouldStickToBottomRef.current = true;
    setShowJumpToLatest(false);
    setProcessingSteps([copy.processing]);

    let voiceMsgId = null;
    let photoRecorded = false;
    let questionRecorded = false;
    const artifactBeforeRequest = currentArtifactRef.current;
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

      const responseArtifact = (response.artifactId || response.artifactName)
        ? {
            id: response.artifactId,
            name: response.artifactName,
            year: response.artifactYear,
            author: response.artifactAuthor,
            summary: response.artifactSummary,
            source: response.answerSource
          }
        : null;

      if (voiceMsgId && response.transcript) {
        setMessages(prev => prev.map(message => (
          message.id === voiceMsgId
            ? { ...message, content: response.transcript }
            : message
        )));
        onPassportQuestion?.({
          text: response.transcript,
          artifact: responseArtifact || artifactBeforeRequest,
          inputType: 'voice',
          hadImage: Boolean(imageBase64)
        });
        questionRecorded = true;
      }

      if (responseArtifact) {
        const localArtifact = currentArtifact?.id === Number(responseArtifact.id) ? currentArtifact : null;
        if (localArtifact) {
          responseArtifact.openHoursVi = localArtifact.openHoursVi;
          responseArtifact.openHoursEn = localArtifact.openHoursEn;
          responseArtifact.ticketVi = localArtifact.ticketVi;
          responseArtifact.ticketEn = localArtifact.ticketEn;
          responseArtifact.highlightVi = localArtifact.highlightVi;
          responseArtifact.highlightEn = localArtifact.highlightEn;
          responseArtifact.images = localArtifact.images;
        }
        setCurrentArtifact(responseArtifact);
        onPassportCheckIn?.(responseArtifact, {
          method: imageBase64 ? 'scan' : 'chat',
          source: imageBase64 ? 'image_recognition' : (voiceMsgId ? 'voice_chat' : 'text_chat')
        });
      }

      if (imageBase64) {
        onPassportPhoto?.({
          imageBase64,
          artifact: responseArtifact || artifactBeforeRequest,
          source: responseArtifact ? 'scan_match' : 'scan'
        });
        photoRecorded = true;
      }

      if (text) {
        onPassportQuestion?.({
          text,
          artifact: responseArtifact || artifactBeforeRequest,
          inputType: 'text',
          hadImage: Boolean(imageBase64)
        });
        questionRecorded = true;
      }

      setProcessingSteps(response.processingSteps || []);

      const aiMsgId = `ai-${Date.now()}`;
      const aiMsg = {
        id: aiMsgId,
        role: 'ai',
        type: 'text',
        content: response.responseText || '',
        speechText: response.speechText || response.responseText || '',
        audioStatus: 'idle',
        timestamp: new Date(),
        source: response.answerSource,
        artifactData: response.artifactId ? {
          artifact_id: response.artifactId,
          artifact_name: response.artifactName
        } : null
      };
      setIsProcessing(false);
      await appendAssistantMessageProgressively(aiMsg);
    } catch (error) {
      if (imageBase64 && !photoRecorded) {
        onPassportPhoto?.({
          imageBase64,
          artifact: artifactBeforeRequest,
          source: 'scan'
        });
      }
      if (text && !questionRecorded) {
        onPassportQuestion?.({
          text,
          artifact: artifactBeforeRequest,
          inputType: 'text',
          hadImage: Boolean(imageBase64)
        });
      }
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

  const handleFindNextStop = async () => {
    const artifact = currentArtifactRef.current;
    if (!artifact?.id || !onRequestNextStop) {
      addErrorMessage('no_next_stop');
      return;
    }

    shouldStickToBottomRef.current = true;
    setShowJumpToLatest(false);
    setProcessingSteps([copy.findingNextStop]);
    setMessages(prev => [...prev, {
      id: `next-q-${Date.now()}`,
      role: 'user',
      type: 'text',
      content: language === 'vi'
        ? `Đi tiếp đâu sau ${artifact.name}?`
        : `Where should I go after ${artifact.name}?`,
      timestamp: new Date()
    }]);

    try {
      const suggestion = await onRequestNextStop(artifact);
      if (!suggestion) {
        addErrorMessage('no_next_stop');
        return;
      }

      const suggestionName = getSuggestionName(suggestion, language);
      setMessages(prev => [...prev, {
        id: `next-a-${Date.now()}`,
        role: 'ai',
        type: 'text',
        content: language === 'vi'
          ? `Sau ${artifact.name}, điểm hợp lý tiếp theo là ${suggestionName}. Bạn có thể xem đường đi hoặc nghe giới thiệu trước.`
          : `After ${artifact.name}, a good next stop is ${suggestionName}. You can view the route or preview the intro first.`,
        timestamp: new Date(),
        source: 'template'
      }]);
    } catch (error) {
      addErrorMessage(error.message);
    } finally {
      setProcessingSteps([]);
    }
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

    if (autoSpeak) {
      // Start speaking as soon as the text is visible using the device voice.
      handleSpeakMessage(message);
    } else if (!autoSpeak) {
      if (onNarrationFinished && currentArtifactRef.current) {
        onNarrationFinished(currentArtifactRef.current);
      }
    }
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
        ? 'Chưa lưu được phản hồi của bạn. Hãy thử lại sau ít phút.'
        : 'Your feedback could not be saved. Try again in a moment.';
    }
    if (lower.includes('no_next_stop')) {
      return copy.noNextStop;
    }
    if (lower.includes('too large') || lower.includes('quá lớn')) {
      return language === 'vi'
        ? 'Ảnh hoặc đoạn ghi âm đang quá lớn. Hãy thử ảnh nhỏ hơn hoặc ghi âm ngắn hơn.'
        : 'The photo or recording is too large. Try a smaller photo or a shorter recording.';
    }
    if (lower.includes('timeout') || lower.includes('quá lâu')) {
      return language === 'vi'
        ? 'Chuẩn bị quá lâu. Hãy thử lại với câu hỏi ngắn hơn.'
        : 'This took too long. Try again with a shorter question.';
    }
    if (lower.includes('provider') || lower.includes('api key')) {
      return language === 'vi'
        ? 'Tính năng giọng nói hoặc nhận diện hiện chưa sẵn sàng. Bạn vẫn có thể nhập câu hỏi bằng chữ.'
        : 'Voice or recognition is not ready yet. You can still type your question.';
    }
    if (lower.includes('failed to fetch') || lower.includes('network') || lower.includes('load failed')) {
      return language === 'vi'
        ? 'Chưa kết nối được hướng dẫn. Hãy kiểm tra mạng rồi thử lại.'
        : 'The guide is not reachable. Check your connection and try again.';
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

  const handleSpeakMessage = async (message) => {
    const isActiveMessage = activeAudioMsgId === message.id;

    if (isActiveMessage && speechState === 'playing') {
      if (pauseTTS()) {
        setSpeechState('paused');
        setMessages(prev => prev.map(m => (
          m.id === message.id ? { ...m, audioStatus: 'paused' } : m
        )));
      }
      return;
    }

    if (isActiveMessage && speechState === 'paused') {
      if (resumeTTS()) {
        setSpeechState('playing');
        setMessages(prev => prev.map(m => (
          m.id === message.id ? { ...m, audioStatus: 'playing' } : m
        )));
      } else {
        handleStopAudio();
        window.setTimeout(() => handleSpeakMessage(message), 0);
      }
      return;
    }

    stopTTS();
    const spokenText = message.content || message.speechText;
    if (spokenText) {
      setActiveAudioMsgId(message.id);
      setSpeechState('playing');
      setMessages(prev => prev.map(m => (
        m.id === message.id ? { ...m, audioStatus: 'playing' } : m
      )));
      playTTS(spokenText, language, () => {
        setActiveAudioMsgId(null);
        setSpeechState('idle');
        setMessages(prev => prev.map(m => (
          m.id === message.id ? { ...m, audioStatus: 'stopped' } : m
        )));
        onPassportAudio?.({
          artifact: currentArtifactRef.current,
          seconds: estimateSpeechSeconds(spokenText),
          title: spokenText,
          source: 'web_speech'
        });
        if (onNarrationFinished && currentArtifactRef.current) {
          onNarrationFinished(currentArtifactRef.current);
        }
      });
    }
  };

  const handleStopAudio = () => {
    const stoppedMsgId = activeAudioMsgId;
    stopTTS();
    setActiveAudioMsgId(null);
    setSpeechState('idle');
    setMessages(prev => prev.map(m => (
      m.id === stoppedMsgId ? { ...m, audioStatus: 'stopped' } : m
    )));
  };

  const handleSelectHistoryAudio = async (item) => {
    const msg = messagesRef.current.find(m => m.id === item.id);
    if (msg) {
      await handleSpeakMessage(msg);
    }
  };

  const formatDuration = (seconds) => {
    if (isNaN(seconds) || seconds === null || seconds === undefined) return '00:00';
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const handleResetConversation = () => {
    shouldStickToBottomRef.current = true;
    setShowJumpToLatest(false);
    handleStopAudio();
    const newId = `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    sessionIdRef.current = newId;
    sessionStorage.setItem('unified_chat_session_id', newId);
    lastInitialArtifactKeyRef.current = null;
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
    { key: 'status', label: language === 'vi' ? 'Chuẩn bị' : 'Preparing', icon: CheckCircle2 }
  ];

  const activePrompts = currentArtifact?.name
    ? getContextPrompts(currentArtifact.name, language)
    : copy.quickPrompts;

  const nextSuggestionName = getSuggestionName(nextSuggestion, language);
  const nextSuggestionMeta = nextSuggestion
    ? [
        nextSuggestion.reason,
        nextSuggestion.distance ? `${Math.round(nextSuggestion.distance)}m` : '',
        nextSuggestion.walk_duration_min
          ? `${Math.ceil(nextSuggestion.walk_duration_min)} ${language === 'vi' ? 'phút đi bộ' : 'min walk'}`
          : ''
      ].filter(Boolean).join(' · ')
    : '';

  const handlePromptClick = (prompt) => {
    if (currentArtifact?.name && prompt === activePrompts[activePrompts.length - 1]) {
      handleFindNextStop();
      return;
    }
    handleSendText(prompt);
  };

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
            <div className="brand-mark"><Landmark size={20} /></div>
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
                {activePrompts.map((prompt) => (
                  <button key={prompt} onClick={() => handlePromptClick(prompt)}>
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

          {currentArtifact?.name && (
            <div className="conversation-context-strip">
              <MapPin size={15} />
              <span>{copy.contextEyebrow}</span>
              <strong>{currentArtifact.name}</strong>
              <button onClick={() => handleSendText(activePrompts[0], currentArtifact.id)}>
                <Volume2 size={14} />
                {copy.listenIntro}
              </button>
              {onRequestNextStop && (
                <button onClick={handleFindNextStop}>
                  <Navigation size={14} />
                  {copy.nextStopQuestion}
                </button>
              )}
            </div>
          )}

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
                {nextSuggestion && (
                  <div className="guide-next-card">
                    <div>
                      <span>{copy.nextStopTitle}</span>
                      <strong>{nextSuggestionName}</strong>
                      {nextSuggestionMeta && <small>{nextSuggestionMeta}</small>}
                    </div>
                    <div className="guide-next-actions">
                      <button onClick={() => onNavigateNextStop?.(nextSuggestion)}>
                        <Navigation size={14} />
                        {copy.showRoute}
                      </button>
                      <button onClick={() => onPreviewNextStop?.(nextSuggestion)}>
                        <Volume2 size={14} />
                        {copy.previewNext}
                      </button>
                    </div>
                  </div>
                )}

                {mobileGuidePanel === 'prompts' && (
                  <div className="mobile-prompt-row">
                    {activePrompts.map((prompt) => (
                      <button key={prompt} onClick={() => handlePromptClick(prompt)}>
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
                      {currentArtifact.images && currentArtifact.images.length > 0 && (
                        <ImageGallery
                          images={currentArtifact.images}
                          className="mini-image-row"
                        />
                      )}
                      <div className="artifact-mini-grid">
                        <div>
                          <span>{copy.year}</span>
                          <strong>{currentArtifact.year || '-'}</strong>
                        </div>
                        <div>
                          <span>{copy.author}</span>
                          <strong>{currentArtifact.author || '-'}</strong>
                        </div>
                        {(currentArtifact.id === 16 || currentArtifact.id === 17) && currentArtifact.openHoursVi && (
                          <div>
                            <span>{language === 'vi' ? 'Giờ mở cửa' : 'Open hours'}</span>
                            <strong>{language === 'vi' ? currentArtifact.openHoursVi : currentArtifact.openHoursEn}</strong>
                          </div>
                        )}
                        {(currentArtifact.id === 16 || currentArtifact.id === 17) && currentArtifact.ticketVi && (
                          <div>
                            <span>{language === 'vi' ? 'Giá vé' : 'Ticket'}</span>
                            <strong>{language === 'vi' ? currentArtifact.ticketVi : currentArtifact.ticketEn}</strong>
                          </div>
                        )}
                      </div>
                      {currentArtifact.highlightVi && (
                        <small style={{ display: 'block', marginBottom: '8px', color: '#9d3f2f', fontWeight: 700, fontSize: '11px' }}>
                          {language === 'vi' ? currentArtifact.highlightVi : currentArtifact.highlightEn}
                        </small>
                      )}
                      <p>{currentArtifact.summary || copy.detailEmpty}</p>
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
                      {message.role === 'ai' && message.type !== 'error' && (() => {
                        const isActive = activeAudioMsgId === message.id;
                        const isCurrentPlaying = isActive && speechState === 'playing';
                        const isCurrentPaused = isActive && speechState === 'paused';
                        return (
                          <button
                            className={`tts-control-btn ${isCurrentPlaying ? 'is-playing' : ''} ${isCurrentPaused ? 'is-paused' : ''}`}
                            onClick={() => handleSpeakMessage(message)}
                            aria-label={isCurrentPlaying ? (language === 'vi' ? 'Tạm dừng' : 'Pause') : isCurrentPaused ? (language === 'vi' ? 'Phát tiếp' : 'Resume') : copy.listen}
                            title={isCurrentPlaying ? (language === 'vi' ? 'Tạm dừng' : 'Pause') : isCurrentPaused ? (language === 'vi' ? 'Phát tiếp' : 'Resume') : copy.listen}
                          >
                            {isCurrentPlaying ? <Pause size={14} /> : isCurrentPaused ? <Play size={14} /> : <Volume2 size={14} />}
                          </button>
                        );
                      })()}
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

          {activeAudioMsgId && (() => {
            const activeMsg = messages.find(m => m.id === activeAudioMsgId) || {};
            const historyItems = messages
              .filter(m => m.role === 'ai' && m.type === 'text' && !m.isStreaming)
              .slice(-3);

            const displayTitle = activeMsg.content 
              ? (activeMsg.content.length > 50 ? activeMsg.content.slice(0, 50) + '...' : activeMsg.content)
              : (language === 'vi' ? 'Đang phát thuyết minh di tích' : 'Playing narration');

            return (
              <div className="bottom-audio-player">
                <div className="audio-player-layout">
                  <div className="audio-player-meta">
                    <div className={`audio-wave-icon ${speechState === 'playing' ? 'wave-playing' : ''}`}>
                      <Volume2 size={16} />
                    </div>
                    <div className="audio-meta-text">
                      <strong>{displayTitle}</strong>
                      <span>{language === 'vi' ? 'Giọng đọc trên thiết bị' : 'Device voice'}</span>
                    </div>
                  </div>

                  <div className="audio-player-controls-section">
                    <div className="audio-playback-buttons">
                      <button 
                        className="play-pause-toggle-btn"
                        onClick={() => handleSpeakMessage(activeMsg)} 
                        title={speechState === 'playing' ? (language === 'vi' ? 'Tạm dừng' : 'Pause') : (language === 'vi' ? 'Phát' : 'Play')}
                        aria-label={speechState === 'playing' ? 'Pause' : 'Play'}
                      >
                        {speechState === 'playing' ? <Pause size={16} /> : <Play size={16} />}
                      </button>
                      <button onClick={handleStopAudio} className="stop-playback-btn" title={language === 'vi' ? 'Dừng phát' : 'Stop'} aria-label="Stop playback">
                        <X size={14} />
                      </button>
                    </div>
                  </div>
                </div>

                {historyItems.length > 0 && (
                  <div className="audio-history-switcher">
                    <span className="switcher-label">
                      <Sparkles size={11} />
                      {language === 'vi' ? '3 câu thoại gần nhất:' : 'Last 3 narrations:'}
                    </span>
                    <div className="history-chips-row">
                      {historyItems.map((item, index) => {
                        const isActive = item.id === activeAudioMsgId;
                        const shortText = item.content.length > 22 ? item.content.slice(0, 22) + '...' : item.content;
                        return (
                          <button 
                            key={item.id} 
                            onClick={() => handleSelectHistoryAudio(item)}
                            className={`history-audio-chip ${isActive ? 'active' : ''}`}
                            title={item.content}
                          >
                            <span className="chip-num">#{index + 1}</span>
                            <span>{shortText}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}

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
                <span className="recording-time">{formatDuration(recordDuration)}</span>
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
                  {currentArtifact.images && currentArtifact.images.length > 0 && (
                    <ImageGallery
                      images={currentArtifact.images}
                      className="desktop-gallery"
                    />
                  )}
                  <div className="artifact-meta-grid">
                    <div>
                      <span>{copy.year}</span>
                      <strong>{currentArtifact.year || '-'}</strong>
                    </div>
                    <div>
                      <span>{copy.author}</span>
                      <strong>{currentArtifact.author || '-'}</strong>
                    </div>
                    {(currentArtifact.id === 16 || currentArtifact.id === 17) && currentArtifact.openHoursVi && (
                      <div>
                        <span>{language === 'vi' ? 'Giờ mở cửa' : 'Open hours'}</span>
                        <strong>{language === 'vi' ? currentArtifact.openHoursVi : currentArtifact.openHoursEn}</strong>
                      </div>
                    )}
                    {(currentArtifact.id === 16 || currentArtifact.id === 17) && currentArtifact.ticketVi && (
                      <div>
                        <span>{language === 'vi' ? 'Giá vé' : 'Ticket'}</span>
                        <strong>{language === 'vi' ? currentArtifact.ticketVi : currentArtifact.ticketEn}</strong>
                      </div>
                    )}
                  </div>
                  {currentArtifact.highlightVi && (
                    <div className="summary-block">
                      <span>{language === 'vi' ? 'Điểm đặc sắc' : 'Highlight'}</span>
                      <p>{language === 'vi' ? currentArtifact.highlightVi : currentArtifact.highlightEn}</p>
                    </div>
                  )}
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
                {activePrompts.slice(0, 3).map((prompt) => (
                  <button key={prompt} onClick={() => handlePromptClick(prompt)}>
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

        .conversation-context-strip {
          display: flex;
          align-items: center;
          gap: 8px;
          min-height: 42px;
          padding: 8px 12px;
          color: var(--ui-text);
          background: #f3fbf8;
          border-bottom: 1px solid rgba(15, 95, 89, 0.16);
        }

        .conversation-context-strip > svg {
          flex: 0 0 auto;
          color: var(--ui-teal);
        }

        .conversation-context-strip span {
          color: var(--ui-muted);
          font-size: 11px;
          font-weight: 900;
          text-transform: uppercase;
          white-space: nowrap;
        }

        .conversation-context-strip strong {
          flex: 1;
          min-width: 0;
          overflow: hidden;
          color: var(--ui-text);
          font-size: 13px;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .conversation-context-strip button {
          flex: 0 0 auto;
          min-height: 30px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 5px;
          border: 1px solid rgba(15, 95, 89, 0.18);
          border-radius: 8px;
          color: var(--ui-teal);
          background: #ffffff;
          padding: 6px 9px;
          font-size: 11px;
          font-weight: 900;
        }

        .conversation-context-strip button:hover {
          background: var(--ui-teal);
          color: #fffdf6;
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

        .desktop-gallery {
          display: flex;
          gap: 6px;
          overflow-x: auto;
          margin-bottom: 12px;
        }

        .desktop-gallery img {
          width: 120px;
          height: 80px;
          object-fit: cover;
          border-radius: 6px;
          border: 1px solid rgba(24, 32, 35, 0.1);
          cursor: pointer;
          transition: transform 0.2s;
        }

        .desktop-gallery img:hover {
          transform: scale(1.05);
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
          font-size: 12px;
          font-weight: 900;
          letter-spacing: 0;
          text-transform: uppercase;
        }

        .artifact-meta-grid strong {
          color: var(--ui-text);
          font-size: 14px;
          line-height: 1.4;
          white-space: pre-line;
        }

        .summary-block p {
          margin: 0;
          color: var(--ui-text);
          font-size: 14px;
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

          .conversation-context-strip {
            flex-wrap: wrap;
            align-items: flex-start;
          }

          .conversation-context-strip strong {
            flex-basis: calc(100% - 92px);
          }

          .conversation-context-strip button {
            flex: 1 1 128px;
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

        .guide-next-card {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
          gap: 9px;
          margin-bottom: 9px;
          border: 1px solid rgba(15, 95, 89, 0.18);
          border-radius: 8px;
          background: #ffffff;
          padding: 11px;
          box-shadow: 0 8px 20px rgba(15, 95, 89, 0.08);
        }

        .guide-next-card span {
          display: block;
          color: var(--ui-teal);
          font-size: 10.5px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .guide-next-card strong {
          display: block;
          margin-top: 2px;
          color: var(--ui-text);
          font-size: 14px;
          line-height: 1.2;
        }

        .guide-next-card small {
          display: block;
          margin-top: 4px;
          color: var(--ui-muted);
          font-size: 11.5px;
          line-height: 1.35;
        }

        .guide-next-actions {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 7px;
        }

        .guide-next-actions button {
          min-width: 0;
          min-height: 38px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          border: 1px solid rgba(15, 95, 89, 0.18);
          border-radius: 8px;
          color: var(--ui-teal);
          background: #f7faf8;
          padding: 8px;
          font-size: 12px;
          font-weight: 900;
        }

        .guide-next-actions button:first-child {
          color: #fffdf6;
          background: var(--ui-teal);
          border-color: var(--ui-teal);
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
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 7px;
          margin-bottom: 10px;
        }

        .mini-image-row {
          display: flex;
          gap: 6px;
          overflow-x: auto;
          margin-bottom: 10px;
        }

        .mini-image-row img {
          width: 90px;
          height: 60px;
          object-fit: cover;
          border-radius: 6px;
          border: 1px solid rgba(24, 32, 35, 0.1);
          cursor: pointer;
          transition: transform 0.2s;
        }

        .mini-image-row img:hover {
          transform: scale(1.08);
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
          font-size: 11px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .artifact-mini-grid strong {
          display: block;
          overflow-wrap: anywhere;
          color: var(--ui-text);
          font-size: 13px;
          line-height: 1.3;
          white-space: pre-line;
        }

        .mobile-artifact-summary p,
        .mobile-empty-note p {
          margin: 0;
          color: var(--ui-text);
          font-size: 13px;
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

        /* Bottom Audio Player styling */
        .bottom-audio-player {
          background: rgba(255, 253, 246, 0.96);
          backdrop-filter: blur(20px);
          border-top: 1px solid var(--ui-border);
          border-bottom: 1px solid var(--ui-border);
          padding: 12px clamp(14px, 2vw, 20px);
          display: flex;
          flex-direction: column;
          gap: 10px;
          box-shadow: 0 -8px 24px rgba(24, 32, 35, 0.05);
          position: relative;
          z-index: 10;
        }

        .audio-player-layout {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          flex-wrap: wrap;
        }

        .audio-player-meta {
          display: flex;
          align-items: center;
          gap: 10px;
          flex: 1;
          min-width: 200px;
        }

        .audio-wave-icon {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: rgba(15, 95, 89, 0.08);
          color: var(--ui-teal);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
        }

        .audio-wave-icon.wave-playing {
          background: var(--ui-teal);
          color: #ffffff;
          animation: audioPulse 1.5s infinite ease-in-out;
        }

        @keyframes audioPulse {
          0% { box-shadow: 0 0 0 0 rgba(15, 95, 89, 0.4); }
          70% { box-shadow: 0 0 0 6px rgba(15, 95, 89, 0); }
          100% { box-shadow: 0 0 0 0 rgba(15, 95, 89, 0); }
        }

        .audio-meta-text {
          display: flex;
          flex-direction: column;
          min-width: 0;
          text-align: left;
        }

        .audio-meta-text strong {
          font-size: 13px;
          color: var(--ui-text);
          font-weight: 700;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .audio-meta-text span {
          font-size: 11px;
          color: var(--ui-muted);
        }

        .audio-player-controls-section {
          display: flex;
          align-items: center;
          gap: 16px;
          flex: 2;
          min-width: 280px;
        }

        .audio-playback-buttons {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .audio-playback-buttons button {
          width: 28px;
          height: 28px;
          border: 1px solid rgba(24, 32, 35, 0.12);
          background: #ffffff;
          color: var(--ui-text);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          padding: 0;
        }

        .audio-playback-buttons button:hover:not(:disabled) {
          border-color: var(--ui-teal);
          color: var(--ui-teal);
          background: var(--ui-surface-muted);
        }

        .audio-playback-buttons button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .audio-playback-buttons .play-pause-toggle-btn {
          width: 34px;
          height: 34px;
          background: var(--ui-teal);
          color: #ffffff;
          border-color: var(--ui-teal);
        }

        .audio-playback-buttons .play-pause-toggle-btn:hover {
          background: var(--ui-teal-2);
          color: #ffffff;
        }

        .audio-playback-buttons .stop-playback-btn:hover {
          background: var(--ui-red);
          color: #ffffff;
          border-color: var(--ui-red);
        }

        .audio-history-switcher {
          display: flex;
          align-items: center;
          gap: 12px;
          border-top: 1px dashed rgba(24, 32, 35, 0.08);
          padding-top: 8px;
          margin-top: 2px;
        }

        .switcher-label {
          font-size: 11px;
          font-weight: 700;
          color: var(--ui-teal);
          display: flex;
          align-items: center;
          gap: 4px;
          flex-shrink: 0;
        }

        .history-chips-row {
          display: flex;
          gap: 8px;
          overflow-x: auto;
          padding-bottom: 2px;
          flex: 1;
        }

        .history-chips-row::-webkit-scrollbar {
          height: 3px;
        }

        .history-chips-row::-webkit-scrollbar-thumb {
          background: rgba(24, 32, 35, 0.1);
          border-radius: 99px;
        }

        .history-audio-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: #ffffff;
          border: 1px solid rgba(24, 32, 35, 0.08);
          border-radius: 99px;
          font-size: 11px;
          color: var(--ui-text);
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
        }

        .history-audio-chip:hover {
          border-color: var(--ui-teal);
          background: rgba(15, 95, 89, 0.04);
        }

        .history-audio-chip.active {
          background: rgba(15, 95, 89, 0.08);
          border-color: var(--ui-teal);
          color: var(--ui-teal);
          font-weight: 700;
        }

        .chip-num {
          font-weight: 800;
          color: var(--ui-muted);
        }

        .history-audio-chip.active .chip-num {
          color: var(--ui-teal);
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
