import React, { useEffect, useRef, useState } from 'react';
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
import { unifiedChatAPI, playTTS, stopTTS, submitFeedbackAPI } from '../../services/apiService';
import { compressImage } from '../../utils/imageUtils';
import CameraScanner from '../CameraScanner';

const COPY = {
  vi: {
    title: 'AI Tour Guide',
    subtitle: 'Hướng dẫn viên số cho hành trình văn hóa',
    status: 'Sẵn sàng',
    back: 'Trang chủ',
    upload: 'Tải ảnh',
    camera: 'Chụp ảnh',
    askPlaceholder: 'Hỏi về hiện vật, lịch sử hoặc địa điểm...',
    greeting: 'Xin chào! Hãy tải ảnh hiện vật, dùng webcam hoặc hỏi trực tiếp về một địa điểm lịch sử.',
    processing: 'Đang chuẩn bị câu trả lời',
    artifactPanel: 'Thông tin hiện vật',
    noArtifact: 'Tải ảnh, chụp hiện vật hoặc đặt câu hỏi để nhận thông tin phù hợp.',
    confidence: 'Độ tin cậy',
    year: 'Năm',
    author: 'Tác giả/triều đại',
    summary: 'Tóm tắt',
    suggestions: 'Gợi ý hỏi nhanh',
    locations: 'Địa điểm nổi bật',
    explore: 'Câu hỏi gợi ý',
    recording: 'Đang ghi âm...',
    transcribing: 'Đang chuyển giọng nói thành văn bản...',
    pendingImage: 'Ảnh chờ gửi',
    detailEmpty: 'Thông tin chi tiết sẽ xuất hiện sau khi tìm thấy hiện vật liên quan.',
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
      'Ngọ Môn được xây năm nào?',
      'Ai xây Điện Thái Hòa?',
      'Kể ngắn về Cửu Đỉnh trong 30 giây',
      'Ý nghĩa lịch sử của Dinh Độc Lập là gì?'
    ],
    locationsList: [
      { name: 'Kinh thành Huế', detail: 'Ngọ Môn, Điện Thái Hòa, Cửu Đỉnh' },
      { name: 'Dinh Độc Lập', detail: 'Phòng Nội các, Hầm chỉ huy, Xe tăng 843' },
      { name: 'Bảo tàng Chứng tích Chiến tranh', detail: 'F-5E Tiger, M48 Patton, UH-1 Huey' }
    ]
  },
  en: {
    title: 'AI Tour Guide',
    subtitle: 'A digital guide for cultural journeys',
    status: 'Ready',
    back: 'Home',
    upload: 'Upload',
    camera: 'Capture',
    askPlaceholder: 'Ask about an artifact, history, or destination...',
    greeting: 'Hello! Upload an artifact photo, use the webcam, or ask about a historical site.',
    processing: 'Preparing your answer',
    artifactPanel: 'Artifact detail',
    noArtifact: 'Upload a photo, capture an artifact, or ask a question to get relevant guidance.',
    confidence: 'Confidence',
    year: 'Year',
    author: 'Author/dynasty',
    summary: 'Summary',
    suggestions: 'Suggested questions',
    locations: 'Featured destinations',
    explore: 'Suggested questions',
    recording: 'Recording...',
    transcribing: 'Transcribing voice...',
    pendingImage: 'Pending image',
    detailEmpty: 'Artifact details will appear after a related item is found.',
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
      'When was Ngo Mon Gate built?',
      'Who built Thai Hoa Palace?',
      'Summarize the Nine Dynastic Urns in 30 seconds',
      'What is the historical meaning of Independence Palace?'
    ],
    locationsList: [
      { name: 'Hue Imperial City', detail: 'Ngo Mon, Thai Hoa Palace, Nine Dynastic Urns' },
      { name: 'Independence Palace', detail: 'Cabinet Room, Command Bunker, Tank 843' },
      { name: 'War Remnants Museum', detail: 'F-5E Tiger, M48 Patton, UH-1 Huey' }
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

const UnifiedChatPage = ({ onBack, language, setLanguage }) => {
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
  const [showJumpToLatest, setShowJumpToLatest] = useState(false);

  const messagesEndRef = useRef(null);
  const messageListRef = useRef(null);
  const shouldStickToBottomRef = useRef(true);
  const sessionIdRef = useRef(null);
  const audioRef = useRef(null);
  const fileInputRef = useRef(null);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioBlob]);

  const processUnifiedChat = async ({ text, audioBlob, imageBase64, filename }) => {
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
        filename
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

      const aiMsg = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        type: 'text',
        content: response.responseText || '',
        audioBlob: response.audioBlob,
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

  const handleSendText = async (overrideText = null) => {
    const text = (overrideText ?? inputText).trim();
    if (!text && !pendingImage) return;
    const image = pendingImage;
    setInputText('');
    setPendingImage(null);
    await processUnifiedChat({ text, imageBase64: image });
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

    if (autoSpeak) {
      handleSpeakMessage(message);
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
        ? 'Trình duyệt không hỗ trợ camera ở chế độ hiện tại. Hãy dùng localhost/HTTPS hoặc tải ảnh lên.'
        : 'Camera access is not supported in the current browser mode. Use localhost/HTTPS or upload a photo.';
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
        ? 'Kết nối đang chậm. Hãy thử lại với câu hỏi ngắn hơn hoặc ảnh rõ hơn.'
        : 'The connection is slow. Try again with a shorter question or a clearer photo.';
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
    // addErrorMessage intentionally reads the current language copy.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordingError, resetRecording]);

  const playAudioBlob = async (blob) => {
    stopTTS();
    if (!blob || blob.size === 0) return false;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audioRef.current = audio;
    try {
      await audio.play();
      audio.onended = () => URL.revokeObjectURL(url);
      return true;
    } catch (err) {
      console.error('Playback failed:', err);
      URL.revokeObjectURL(url);
      return false;
    }
  };

  const handleSpeakMessage = async (message) => {
    let played = false;
    if (message.audioBlob && message.audioBlob.size > 0) {
      played = await playAudioBlob(message.audioBlob);
    }
    if (!played && message.content) {
      playTTS(message.content, language);
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

  return (
    <div className="tour-workspace">
      <header className="tour-topbar">
        <button className="topbar-back" onClick={onBack} aria-label={copy.back}>
          <ArrowLeft size={18} />
          <span>{copy.back}</span>
        </button>
        <div className="brand-block">
          <div className="brand-mark"><Landmark size={22} /></div>
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

      <main className="workspace-grid">
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

        <section className="conversation-panel">
          <div className="conversation-header">
            <div>
              <span className="eyebrow">{copy.assistantEyebrow}</span>
              <h2>{copy.title}</h2>
            </div>
            <div className="conversation-tools">
              <button onClick={() => setShowCamera(true)} aria-label={copy.camera}>
                <Camera size={18} />
                {copy.camera}
              </button>
              <button onClick={() => fileInputRef.current?.click()} aria-label={copy.upload}>
                <Upload size={18} />
                {copy.upload}
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
                        <button onClick={() => handleSpeakMessage(message)} aria-label={copy.listen}>
                          <Volume2 size={14} />
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
          height: 100dvh;
          background: #f5f1e8;
          color: #1f2a2e;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .tour-topbar {
          height: 72px;
          display: flex;
          align-items: center;
          gap: 18px;
          padding: 0 24px;
          background: #fffdf7;
          border-bottom: 1px solid #ded6c5;
        }
        .topbar-back,
        .topbar-icon,
        .conversation-tools button,
        .composer-row button,
        .recording-bar button,
        .camera-header button {
          border: 1px solid #d8cdb9;
          background: #fffaf0;
          color: #254247;
          border-radius: 8px;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 9px 12px;
          font-weight: 650;
        }
        .topbar-icon {
          width: 38px;
          height: 38px;
          justify-content: center;
          padding: 0;
        }
        .topbar-icon.active {
          background: #e4f1ed;
          color: #116149;
        }
        .brand-block {
          display: flex;
          align-items: center;
          gap: 12px;
          flex: 1;
          min-width: 260px;
        }
        .brand-mark {
          width: 42px;
          height: 42px;
          border-radius: 10px;
          background: #1f5f5b;
          color: #fffaf0;
          display: grid;
          place-items: center;
        }
        .brand-block h1 {
          font-size: 19px;
          margin: 0;
        }
        .brand-block p {
          margin: 2px 0 0;
          color: #69716d;
          font-size: 13px;
        }
        .topbar-actions {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .backend-status {
          color: #116149;
          font-size: 13px;
          font-weight: 700;
          display: flex;
          align-items: center;
          gap: 7px;
        }
        .status-dot {
          width: 9px;
          height: 9px;
          border-radius: 999px;
          background: #2f9d69;
        }
        .workspace-grid {
          flex: 1;
          min-height: 0;
          height: calc(100dvh - 72px);
          overflow: hidden;
          display: grid;
          grid-template-columns: minmax(240px, 280px) minmax(420px, 1fr) minmax(300px, 360px);
          gap: 18px;
          padding: 18px;
        }
        .explore-panel,
        .conversation-panel,
        .artifact-panel {
          min-height: 0;
        }
        .explore-panel,
        .artifact-panel {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .panel-section,
        .artifact-card,
        .steps-card,
        .conversation-panel {
          background: #fffdf7;
          border: 1px solid #ded6c5;
          border-radius: 10px;
          box-shadow: 0 10px 26px rgba(66, 49, 24, 0.08);
        }
        .panel-section,
        .artifact-card,
        .steps-card {
          padding: 16px;
        }
        .section-heading {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #1f5f5b;
          margin-bottom: 12px;
        }
        .section-heading h2 {
          margin: 0;
          font-size: 15px;
        }
        .location-list,
        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: 9px;
        }
        .location-card,
        .quick-actions button {
          text-align: left;
          border: 1px solid #e0d5c2;
          background: #fffaf0;
          border-radius: 8px;
          padding: 11px;
          color: #263437;
        }
        .location-card.selected {
          border-color: #1f5f5b;
          box-shadow: inset 3px 0 0 #1f5f5b;
        }
        .location-card strong {
          display: block;
          font-size: 14px;
          margin-bottom: 5px;
        }
        .location-card span,
        .muted {
          color: #6b746f;
          font-size: 13px;
          line-height: 1.45;
        }
        .conversation-panel {
          display: flex;
          flex-direction: column;
          overflow: hidden;
          position: relative;
        }
        .conversation-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 16px 18px;
          border-bottom: 1px solid #ebe2d0;
        }
        .conversation-header h2 {
          margin: 3px 0 0;
          font-size: 18px;
        }
        .eyebrow {
          color: #9b5a2e;
          font-size: 12px;
          font-weight: 800;
          text-transform: uppercase;
        }
        .conversation-tools {
          display: flex;
          gap: 8px;
        }
        .message-list {
          flex: 1;
          min-height: 0;
          overflow-y: auto;
          overscroll-behavior: contain;
          scroll-behavior: smooth;
          padding: 18px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          background: linear-gradient(180deg, #fffdf7 0%, #f8f2e7 100%);
        }
        .message-list::-webkit-scrollbar {
          width: 10px;
        }
        .message-list::-webkit-scrollbar-track {
          background: #f4ead8;
        }
        .message-list::-webkit-scrollbar-thumb {
          background: #c8b99e;
          border-radius: 999px;
          border: 2px solid #f4ead8;
        }
        .message {
          max-width: 76%;
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .message.user {
          align-self: flex-end;
        }
        .message.ai,
        .message.error {
          align-self: flex-start;
        }
        .message-body {
          display: flex;
          gap: 8px;
          align-items: flex-start;
          padding: 12px 13px;
          border-radius: 10px;
          background: #ffffff;
          border: 1px solid #e7dcc9;
          box-shadow: 0 4px 12px rgba(66, 49, 24, 0.06);
        }
        .message.user .message-body {
          background: #1f5f5b;
          color: #ffffff;
          border-color: #1f5f5b;
        }
        .message.error .message-body {
          border-color: #d97b67;
          background: #fff2ed;
        }
        .message-body p {
          margin: 0;
          line-height: 1.55;
          white-space: pre-wrap;
        }
        .stream-caret {
          width: 7px;
          height: 18px;
          background: #1f5f5b;
          display: inline-block;
          border-radius: 999px;
          animation: blink 0.9s steps(2, start) infinite;
          margin-top: 2px;
        }
        @keyframes blink {
          50% { opacity: 0; }
        }
        .message-body button {
          color: #1f5f5b;
          padding: 2px;
        }
        .message.image img {
          max-width: 260px;
          border-radius: 10px;
          border: 1px solid #e0d5c2;
        }
        .message time {
          color: #7d847e;
          font-size: 11px;
        }
        .message.user time {
          text-align: right;
        }
        .message-feedback {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #6b746f;
          font-size: 12px;
        }
        .message-feedback button {
          border: 1px solid #e0d5c2;
          background: #fffaf0;
          color: #425054;
          border-radius: 999px;
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 5px 8px;
          font-size: 12px;
          font-weight: 700;
        }
        .message-feedback span {
          color: #116149;
          font-weight: 700;
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
        .composer {
          border-top: 1px solid #e7dcc9;
          padding: 14px;
          background: #fffdf7;
          flex-shrink: 0;
          position: relative;
          z-index: 2;
        }
        .jump-latest {
          position: absolute;
          right: 18px;
          bottom: 86px;
          z-index: 3;
          border: 1px solid #d8cdb9;
          background: #1f5f5b;
          color: #ffffff;
          border-radius: 999px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          font-size: 13px;
          font-weight: 800;
          box-shadow: 0 10px 24px rgba(31, 95, 91, 0.22);
        }
        .pending-image {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
          padding: 8px;
          background: #f4ead8;
          border-radius: 8px;
        }
        .pending-image img {
          width: 46px;
          height: 46px;
          object-fit: cover;
          border-radius: 6px;
        }
        .pending-image span {
          flex: 1;
          font-size: 13px;
          font-weight: 700;
        }
        .composer-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .composer-row input {
          flex: 1;
          height: 42px;
          border: 1px solid #d8cdb9;
          border-radius: 9px;
          padding: 0 12px;
          color: #1f2a2e;
          background: #fffaf0;
        }
        .send-button {
          background: #9b4d2d !important;
          color: #ffffff !important;
          border-color: #9b4d2d !important;
        }
        .send-button:disabled {
          opacity: 0.45;
        }
        .mic-button {
          background: #1f5f5b !important;
          color: #ffffff !important;
          border-color: #1f5f5b !important;
        }
        .recording-bar {
          display: flex;
          align-items: center;
          gap: 14px;
          background: #fff2ed;
          border: 1px solid #d97b67;
          border-radius: 9px;
          padding: 10px;
        }
        .recording-left {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
          color: #9b3a2c;
        }
        .recording-dot {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #c84736;
        }
        .artifact-card,
        .steps-card {
          overflow: hidden;
        }
        .artifact-visual,
        .empty-artifact {
          border: 1px dashed #d4c7b2;
          background: #f7eddb;
          border-radius: 10px;
          min-height: 120px;
          display: grid;
          place-items: center;
          color: #1f5f5b;
          text-align: center;
          padding: 18px;
        }
        .artifact-card h3 {
          margin: 14px 0 12px;
          font-size: 22px;
          color: #1f2a2e;
        }
        .artifact-meta-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 9px;
          margin-bottom: 14px;
        }
        .artifact-meta-grid div {
          background: #fffaf0;
          border: 1px solid #e0d5c2;
          border-radius: 8px;
          padding: 9px;
        }
        .artifact-meta-grid span,
        .summary-block span {
          display: block;
          color: #777f79;
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
          margin-bottom: 5px;
        }
        .artifact-meta-grid strong {
          font-size: 13px;
          line-height: 1.35;
        }
        .summary-block {
          background: #f8f2e7;
          border-radius: 8px;
          padding: 11px;
        }
        .summary-block p {
          margin: 0;
          line-height: 1.5;
          font-size: 14px;
        }
        .processing-steps {
          margin: 0;
          padding-left: 20px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          color: #334143;
          font-size: 14px;
        }
        .camera-overlay {
          position: fixed;
          inset: 0;
          z-index: 100;
          background: #000;
          display: flex;
          flex-direction: column;
        }
        .camera-header {
          padding: 12px 16px;
          background: rgba(0,0,0,0.82);
          display: flex;
          justify-content: flex-start;
        }
        .camera-header button {
          color: white;
          background: rgba(255,255,255,0.12);
          border-color: rgba(255,255,255,0.2);
        }
        @media (max-width: 1120px) {
          .workspace-grid {
            grid-template-columns: 230px 1fr;
          }
          .artifact-panel {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: 1fr 1fr;
          }
        }

        .tour-workspace {
          --ui-bg: #f7f7f4;
          --ui-surface: #ffffff;
          --ui-surface-muted: #faf9f5;
          --ui-surface-strong: #f3f4f6;
          --ui-text: #111827;
          --ui-muted: #6b7280;
          --ui-border: #e5e7eb;
          --ui-border-strong: #d1d5db;
          --ui-primary: #fece14;
          --ui-primary-border: #eab308;
          --ui-success: #16a34a;
          --ui-danger: #dc2626;
          height: 100dvh;
          background: var(--ui-bg);
          color: var(--ui-text);
          font-family: 'Poppins', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .tour-topbar {
          height: 68px;
          gap: 16px;
          padding: 0 20px;
          background: var(--ui-surface);
          border-bottom: 1px solid var(--ui-border);
        }

        .topbar-back,
        .topbar-icon,
        .conversation-tools button,
        .composer-row button,
        .recording-bar button,
        .camera-header button {
          min-height: 36px;
          border: 1px solid var(--ui-border);
          background: var(--ui-surface);
          color: var(--ui-text);
          border-radius: 8px;
          padding: 8px 11px;
          font-size: 13px;
          font-weight: 700;
          line-height: 1;
          box-shadow: none;
          transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
        }

        .topbar-back:hover,
        .topbar-icon:hover,
        .conversation-tools button:hover,
        .composer-row button:hover,
        .recording-bar button:hover {
          background: var(--ui-surface-strong);
          border-color: var(--ui-border-strong);
        }

        .topbar-back:active,
        .topbar-icon:active,
        .conversation-tools button:active,
        .composer-row button:active,
        .recording-bar button:active {
          transform: translateY(1px);
        }

        .topbar-icon {
          width: 36px;
          height: 36px;
          padding: 0;
        }

        .topbar-icon.active {
          background: #fff8d9;
          color: var(--ui-text);
          border-color: var(--ui-primary-border);
        }

        .brand-block {
          gap: 11px;
          min-width: 220px;
        }

        .brand-mark {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: var(--ui-primary);
          color: var(--ui-text);
        }

        .brand-block h1 {
          color: var(--ui-text);
          font-size: 18px;
          letter-spacing: 0;
        }

        .brand-block p {
          color: var(--ui-muted);
          font-size: 13px;
        }

        .backend-status {
          color: var(--ui-text);
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          padding: 8px 10px;
          background: var(--ui-surface-muted);
          font-size: 12px;
        }

        .status-dot {
          background: var(--ui-success);
          box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.12);
        }

        .tour-workspace .language-toggle {
          background: var(--ui-surface-strong);
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          padding: 4px;
          gap: 4px;
        }

        .tour-workspace .lang-btn {
          border-radius: 6px;
          color: var(--ui-muted);
          padding: 6px 10px;
          font-size: 12px;
          font-weight: 800;
        }

        .tour-workspace .lang-btn.active {
          background: var(--ui-text);
          color: #ffffff;
          box-shadow: none;
        }

        .workspace-grid {
          height: calc(100dvh - 68px);
          grid-template-columns: minmax(240px, 286px) minmax(440px, 1fr) minmax(300px, 348px);
          gap: 16px;
          padding: 16px;
          background: var(--ui-bg);
        }

        .explore-panel,
        .artifact-panel {
          gap: 12px;
        }

        .panel-section,
        .artifact-card,
        .steps-card,
        .conversation-panel {
          background: var(--ui-surface);
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          box-shadow: 0 8px 22px rgba(17, 24, 39, 0.05);
        }

        .panel-section,
        .artifact-card,
        .steps-card {
          padding: 14px;
        }

        .section-heading {
          color: var(--ui-text);
          gap: 8px;
          margin-bottom: 12px;
        }

        .section-heading svg {
          color: var(--ui-text);
          background: var(--ui-primary);
          border-radius: 6px;
          padding: 3px;
          width: 22px;
          height: 22px;
        }

        .section-heading h2 {
          color: var(--ui-text);
          font-size: 14px;
          letter-spacing: 0;
        }

        .location-list,
        .quick-actions {
          gap: 8px;
        }

        .location-card,
        .quick-actions button {
          border: 1px solid var(--ui-border);
          background: var(--ui-surface-muted);
          border-radius: 8px;
          padding: 10px;
          color: var(--ui-text);
          transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
        }

        .location-card:hover,
        .quick-actions button:hover {
          background: #fff8d9;
          border-color: var(--ui-primary-border);
          transform: translateY(-1px);
        }

        .location-card.selected {
          border-color: var(--ui-text);
          background: #fff8d9;
          box-shadow: inset 3px 0 0 var(--ui-primary);
        }

        .location-card strong {
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

        .conversation-header {
          padding: 14px 16px;
          border-bottom: 1px solid var(--ui-border);
          background: var(--ui-surface);
        }

        .conversation-header h2 {
          color: var(--ui-text);
          font-size: 17px;
          letter-spacing: 0;
        }

        .eyebrow {
          color: var(--ui-muted);
          font-size: 11px;
          letter-spacing: 0;
        }

        .conversation-tools {
          gap: 8px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }

        .message-list {
          background: #fbfbf8;
          padding: 16px;
          gap: 12px;
        }

        .message-list::-webkit-scrollbar-track {
          background: #f3f4f6;
        }

        .message-list::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-color: #f3f4f6;
        }

        .message {
          max-width: min(78%, 760px);
        }

        .message-body {
          background: var(--ui-surface);
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          box-shadow: 0 6px 18px rgba(17, 24, 39, 0.05);
          color: var(--ui-text);
          padding: 11px 12px;
        }

        .message.user .message-body {
          background: var(--ui-text);
          color: #ffffff;
          border-color: var(--ui-text);
        }

        .message.error .message-body {
          border-color: rgba(220, 38, 38, 0.35);
          background: #fff1f2;
          color: #991b1b;
        }

        .message-body p {
          font-size: 14px;
          line-height: 1.58;
        }

        .message-body button {
          color: var(--ui-muted);
          border-radius: 6px;
        }

        .message-body button:hover {
          background: var(--ui-surface-strong);
          color: var(--ui-text);
        }

        .message.user .message-body button {
          color: #ffffff;
        }

        .stream-caret {
          background: var(--ui-primary);
        }

        .message.image img {
          max-width: 280px;
          border-radius: 8px;
          border: 1px solid var(--ui-border);
          box-shadow: 0 8px 22px rgba(17, 24, 39, 0.08);
        }

        .message time {
          color: var(--ui-muted);
          font-size: 11px;
        }

        .message-feedback {
          gap: 7px;
          color: var(--ui-muted);
        }

        .message-feedback button {
          border: 1px solid var(--ui-border);
          background: var(--ui-surface);
          color: var(--ui-text);
          border-radius: 8px;
          padding: 6px 8px;
          font-size: 12px;
        }

        .message-feedback button:hover {
          background: #fff8d9;
          border-color: var(--ui-primary-border);
        }

        .message-feedback span {
          color: var(--ui-success);
        }

        .composer {
          border-top: 1px solid var(--ui-border);
          padding: 12px;
          background: var(--ui-surface);
        }

        .jump-latest {
          right: 16px;
          bottom: 78px;
          background: var(--ui-text);
          color: #ffffff;
          border: 1px solid var(--ui-text);
          border-radius: 8px;
          box-shadow: 0 10px 22px rgba(17, 24, 39, 0.18);
        }

        .pending-image {
          background: var(--ui-surface-muted);
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          padding: 8px;
        }

        .pending-image img {
          border-radius: 6px;
        }

        .pending-image button {
          width: 30px;
          height: 30px;
          border-radius: 6px;
          color: var(--ui-muted);
        }

        .pending-image button:hover {
          background: #fee2e2;
          color: var(--ui-danger);
        }

        .composer-row {
          gap: 8px;
          min-width: 0;
        }

        .composer-row button {
          width: 40px;
          height: 40px;
          min-width: 40px;
          justify-content: center;
          padding: 0;
        }

        .composer-row input {
          min-width: 0;
          height: 40px;
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          background: var(--ui-surface-muted);
          color: var(--ui-text);
          padding: 0 12px;
          font-size: 14px;
        }

        .composer-row input::placeholder {
          color: #9ca3af;
        }

        .composer-row input:focus {
          background: var(--ui-surface);
          border-color: var(--ui-primary-border);
        }

        .send-button {
          background: var(--ui-primary) !important;
          color: var(--ui-text) !important;
          border-color: var(--ui-primary-border) !important;
        }

        .send-button:disabled {
          opacity: 0.48;
          cursor: not-allowed;
          transform: none;
        }

        .composer-row .mic-button {
          width: 40px;
          height: 40px;
          min-width: 40px;
          border-radius: 8px;
          background: var(--ui-text) !important;
          color: #ffffff !important;
          border-color: var(--ui-text) !important;
          animation: none;
          box-shadow: none;
          transform: none;
        }

        .composer-row .mic-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .recording-bar {
          border: 1px solid rgba(220, 38, 38, 0.3);
          background: #fff1f2;
          border-radius: 8px;
          padding: 9px 10px;
        }

        .recording-left {
          color: #991b1b;
        }

        .recording-dot {
          background: var(--ui-danger);
          box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.12);
        }

        .recording-time {
          color: var(--ui-text);
          font-variant-numeric: tabular-nums;
          font-weight: 800;
        }

        .recording-bar button {
          background: var(--ui-danger);
          border-color: var(--ui-danger);
          color: #ffffff;
        }

        .artifact-visual,
        .empty-artifact {
          border: 1px dashed var(--ui-border-strong);
          background: var(--ui-surface-muted);
          border-radius: 8px;
          color: var(--ui-text);
          min-height: 118px;
        }

        .empty-artifact {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .empty-artifact p {
          color: var(--ui-muted);
          line-height: 1.5;
          margin: 0;
          max-width: 260px;
        }

        .artifact-card h3 {
          color: var(--ui-text);
          font-size: 20px;
          letter-spacing: 0;
        }

        .artifact-meta-grid {
          gap: 8px;
          margin-bottom: 12px;
        }

        .artifact-meta-grid div {
          background: var(--ui-surface-muted);
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          padding: 9px;
        }

        .artifact-meta-grid span,
        .summary-block span {
          color: var(--ui-muted);
          letter-spacing: 0;
          font-size: 11px;
        }

        .artifact-meta-grid strong {
          color: var(--ui-text);
          font-size: 13px;
        }

        .summary-block {
          background: var(--ui-surface-muted);
          border: 1px solid var(--ui-border);
          border-radius: 8px;
          padding: 10px;
        }

        .summary-block p {
          color: var(--ui-text);
          font-size: 13px;
          line-height: 1.5;
        }

        .processing-steps {
          color: var(--ui-text);
          font-size: 13px;
          gap: 7px;
        }

        .camera-header button {
          background: rgba(255, 255, 255, 0.12);
          border-color: rgba(255, 255, 255, 0.24);
          color: #ffffff;
        }

        .tour-workspace button:focus-visible,
        .tour-workspace input:focus-visible {
          outline: 3px solid rgba(254, 206, 20, 0.42);
          outline-offset: 2px;
        }

        @media (max-width: 1260px) {
          .workspace-grid {
            grid-template-columns: minmax(220px, 260px) minmax(420px, 1fr);
          }

          .artifact-panel {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr);
          }
        }

        @media (max-width: 920px) {
          .tour-workspace {
            overflow-y: auto;
          }

          .tour-topbar {
            height: auto;
            min-height: 68px;
            flex-wrap: wrap;
            align-items: flex-start;
            padding: 12px 14px;
          }

          .brand-block {
            order: 1;
            flex: 1 1 240px;
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

          .conversation-panel {
            min-height: 620px;
          }

          .artifact-panel {
            grid-column: auto;
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 640px) {
          .tour-topbar {
            gap: 10px;
          }

          .backend-status {
            display: none;
          }

          .topbar-actions {
            justify-content: space-between;
          }

          .conversation-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .conversation-tools {
            width: 100%;
            justify-content: stretch;
          }

          .conversation-tools button {
            flex: 1;
            justify-content: center;
          }

          .message {
            max-width: 92%;
          }

          .composer-row {
            flex-wrap: wrap;
          }

          .composer-row input {
            flex: 1 1 100%;
            order: -1;
          }
        }
      `}</style>
    </div>
  );
};

export default UnifiedChatPage;
