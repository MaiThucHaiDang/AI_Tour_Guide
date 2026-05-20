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

const UnifiedChatPage = ({ onBack, language, setLanguage }) => {
  const copy = COPY[language] || COPY.vi;
  const [messages, setMessages] = useState([]);
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

    setMessages([{
      id: 'welcome',
      role: 'ai',
      type: 'text',
      content: copy.greeting,
      timestamp: new Date(),
      source: 'template'
    }]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

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
    if (lower.includes('failed to fetch') || lower.includes('network')) {
      return language === 'vi'
        ? 'Chưa kết nối được với hướng dẫn viên. Hãy đợi vài giây rồi thử lại.'
        : 'The guide is not reachable yet. Wait a few seconds and try again.';
    }
    return message || (language === 'vi'
      ? 'Mình chưa xử lý được yêu cầu này. Hãy thử hỏi ngắn hơn hoặc gửi ảnh rõ hơn.'
      : 'I could not handle this request. Try a shorter question or a clearer photo.');
  };

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
    setMessages([{
      id: 'welcome',
      role: 'ai',
      type: 'text',
      content: copy.greeting,
      timestamp: new Date(),
      source: 'template'
    }]);
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

  const handleFeedback = (message, value) => {
    setMessages(prev => prev.map(item => (
      item.id === message.id ? { ...item, feedback: value } : item
    )));
    submitFeedbackAPI({
      sessionId: sessionIdRef.current,
      messageId: message.id,
      artifactId: message.artifactData?.artifact_id || currentArtifact?.id || null,
      rating: value === 'up' ? 'helpful' : 'not_helpful'
    }).catch(() => undefined);
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
                <button className="mic-button" onMouseDown={startRecording} onTouchStart={startRecording} aria-label={copy.record}>
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
          <CameraScanner onCapture={handleCapture} />
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
      `}</style>
    </div>
  );
};

export default UnifiedChatPage;
