import React, { useState, useEffect, useRef } from 'react';
import { Camera, Mic, Send, Volume2, VolumeX, Image as ImageIcon, ArrowLeft, Loader2, Play, Pause } from 'lucide-react';
import LanguageToggle from '../shared/LanguageToggle';
import VoiceRecorder from './VoiceRecorder';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import { voiceChatAPI, recognizeArtifactAPI, playTTS, stopTTS } from '../../services/apiService';
import { compressImage } from '../../utils/imageUtils';
import CameraScanner from '../CameraScanner';

const UnifiedChatPage = ({ onBack, language, setLanguage }) => {
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [inputText, setInputText] = useState('');
  const [showCamera, setShowCamera] = useState(false);
  const [artifactContext, setArtifactContext] = useState(null);
  
  const messagesEndRef = useRef(null);
  const sessionIdRef = useRef(null);
  const audioRef = useRef(null);

  // Initialize Session ID
  useEffect(() => {
    const cached = sessionStorage.getItem('unified_chat_session_id');
    if (cached) {
      sessionIdRef.current = cached;
    } else {
      const newId = `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      sessionIdRef.current = newId;
      sessionStorage.setItem('unified_chat_session_id', newId);
    }

    // Chào mừng người dùng
    const welcomeMsg = {
      id: 'welcome',
      role: 'ai',
      type: 'text',
      content: language === 'vi' 
        ? 'Xin chào! Tôi là hướng dẫn viên AI của bạn. Hãy gửi ảnh di tích hoặc đặt câu hỏi cho tôi nhé.' 
        : 'Hello! I am your AI tour guide. Feel free to send artifact photos or ask me anything.',
      timestamp: new Date()
    };
    setMessages([welcomeMsg]);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, isProcessing]);

  // --- VOICE HANDLING ---
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
    if (audioBlob) {
      handleVoiceMessage(audioBlob);
    }
  }, [audioBlob]);

  const handleVoiceMessage = async (blob) => {
    const userMsg = {
      id: Date.now(),
      role: 'user',
      type: 'audio',
      content: 'Ghi âm giọng nói',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      const response = await voiceChatAPI(
        blob,
        language,
        null,
        getFilename(),
        sessionIdRef.current,
        artifactContext?.artifact_id,
        artifactContext?.artifact_name
      );

      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        type: 'text',
        content: response.responseText,
        audioBlob: response.audioBlob,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMsg]);
      
      if (autoSpeak && response.audioBlob) {
        playAudioBlob(response.audioBlob);
      }
    } catch (error) {
      addErrorMessage(error.message);
    } finally {
      setIsProcessing(false);
      resetRecording();
    }
  };

  // --- IMAGE HANDLING ---
  const handleCapture = async (photoBase64) => {
    setShowCamera(false);
    const userMsg = {
      id: Date.now(),
      role: 'user',
      type: 'image',
      content: photoBase64,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      // Add status message
      const statusMsgId = 'status-' + Date.now();
      setMessages(prev => [...prev, {
        id: statusMsgId,
        role: 'ai',
        type: 'status',
        content: language === 'vi' ? 'Đang truy xuất thông tin hiện vật...' : 'Retrieving artifact information...',
        timestamp: new Date()
      }]);

      const compressed = await compressImage(photoBase64, 800, 800, 0.7);
      const response = await recognizeArtifactAPI(compressed, language, sessionIdRef.current);

      // Remove status message
      setMessages(prev => prev.filter(m => m.id !== statusMsgId));

      if (response.status === 'success') {
        const aiMsg = {
          id: Date.now() + 1,
          role: 'ai',
          type: 'text',
          content: response.data.text_response,
          timestamp: new Date(),
          isResult: true,
          artifactData: response.data
        };
        setMessages(prev => [...prev, aiMsg]);
        setArtifactContext(response.data);

        if (autoSpeak) {
          playTTS(response.data.text_response);
        }
      } else {
        addErrorMessage(response.message);
      }
    } catch (error) {
      addErrorMessage(error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  // --- TEXT HANDLING ---
  const handleSendText = async () => {
    if (!inputText.trim()) return;

    const text = inputText.trim();
    setInputText('');
    
    const userMsg = {
      id: Date.now(),
      role: 'user',
      type: 'text',
      content: text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      // Vì hiện tại ta chưa có API chat text riêng, ta sẽ dùng voiceChatAPI 
      // nhưng gửi một blob rỗng (cần Backend hỗ trợ hoặc tạo mock blob)
      // Tạm thời ta giả lập bằng cách gọi voiceChatAPI với một ghi âm im lặng 
      // hoặc chỉnh Backend để hỗ trợ TEXT chat.
      // TRONG BÀI NÀY: Giả định ta dùng voiceChatAPI nhưng gửi kèm text hint (nếu có)
      // Tuy nhiên, cách tốt nhất là Backend nên có 1 endpoint /chat/text.
      
      // MOCK PHẢN HỒI CHO TEXT (Vì backend hiện tại chủ yếu là Audio/Vision)
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        type: 'text',
        content: language === 'vi' 
          ? `Tôi đã nhận được câu hỏi: "${text}". Hiện tại tôi đang được tối ưu để trả lời qua giọng nói và hình ảnh.` 
          : `I received your question: "${text}". Currently I am optimized for voice and image interaction.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  const addErrorMessage = (msg) => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'ai',
      type: 'error',
      content: msg || 'Đã có lỗi xảy ra.',
      timestamp: new Date()
    }]);
  };

  const playAudioBlob = (blob) => {
    stopTTS();
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.play();
  };

  const handleSpeakMessage = (msg) => {
    if (msg.audioBlob) {
      playAudioBlob(msg.audioBlob);
    } else if (msg.content) {
      playTTS(msg.content);
    }
  };

  return (
    <div className="unified-chat-page">
      {/* Header */}
      <div className="chat-header">
        <button className="icon-btn" onClick={onBack}>
          <ArrowLeft size={24} />
        </button>
        <div className="header-info">
          <h3>AI Tour Guide</h3>
          <span className="status-dot"></span>
        </div>
        <div className="header-actions">
          <button 
            className={`icon-btn ${autoSpeak ? 'active' : ''}`} 
            onClick={() => setAutoSpeak(!autoSpeak)}
            title={autoSpeak ? 'Auto-speak ON' : 'Auto-speak OFF'}
          >
            {autoSpeak ? <Volume2 size={20} /> : <VolumeX size={20} />}
          </button>
          <LanguageToggle language={language} setLanguage={setLanguage} />
        </div>
      </div>

      {/* Message List */}
      <div className="message-list">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-bubble ${msg.role}`}>
            {msg.type === 'image' ? (
              <div className="image-content">
                <img src={msg.content} alt="User upload" />
              </div>
            ) : msg.type === 'status' ? (
              <div className="status-content">
                <Loader2 className="animate-spin" size={16} />
                <span>{msg.content}</span>
              </div>
            ) : (
              <div className="text-content">
                {msg.content}
                {msg.role === 'ai' && msg.type !== 'error' && (
                  <button className="msg-speak-btn" onClick={() => handleSpeakMessage(msg)}>
                    <Volume2 size={14} />
                  </button>
                )}
              </div>
            )}
            <div className="message-time">
              {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="message-bubble ai typing">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <button className="action-btn" onClick={() => setShowCamera(true)}>
          <Camera size={24} />
        </button>
        
        <div className="input-wrapper">
          <input 
            type="text" 
            placeholder={language === 'vi' ? 'Hỏi tôi điều gì đó...' : 'Ask me anything...'} 
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendText()}
          />
          <button className="send-btn" onClick={handleSendText} disabled={!inputText.trim()}>
            <Send size={20} />
          </button>
        </div>

        <div className="voice-btn-container">
          <button 
            className={`voice-btn ${isRecording ? 'recording' : ''}`}
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
          >
            <Mic size={24} />
            {isRecording && <div className="recording-ring"></div>}
          </button>
        </div>
      </div>

      {/* Camera Overlay */}
      {showCamera && (
        <div className="camera-overlay">
          <div className="camera-header">
            <button className="close-btn" onClick={() => setShowCamera(false)}>
              <ArrowLeft size={24} /> {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
          </div>
          <CameraScanner onCapture={handleCapture} />
        </div>
      )}

      <style jsx>{`
        .unified-chat-page {
          display: flex;
          flex-direction: column;
          height: 100vh;
          background: #f0f2f5;
          position: relative;
        }
        .chat-header {
          display: flex;
          align-items: center;
          padding: 10px 15px;
          background: white;
          box-shadow: 0 1px 2px rgba(0,0,0,0.1);
          z-index: 10;
        }
        .header-info {
          flex: 1;
          margin-left: 10px;
        }
        .header-info h3 {
          margin: 0;
          font-size: 16px;
        }
        .status-dot {
          display: inline-block;
          width: 8px;
          height: 8px;
          background: #4caf50;
          border-radius: 50%;
          margin-right: 5px;
        }
        .header-actions {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .icon-btn {
          background: none;
          border: none;
          padding: 8px;
          border-radius: 50%;
          cursor: pointer;
          color: #65676b;
        }
        .icon-btn.active {
          color: #0084ff;
          background: rgba(0,132,255,0.1);
        }
        .message-list {
          flex: 1;
          overflow-y: auto;
          padding: 15px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .message-bubble {
          max-width: 80%;
          padding: 10px 15px;
          border-radius: 18px;
          font-size: 15px;
          position: relative;
          word-wrap: break-word;
        }
        .message-bubble.user {
          align-self: flex-end;
          background: #0084ff;
          color: white;
          border-bottom-right-radius: 4px;
        }
        .message-bubble.ai {
          align-self: flex-start;
          background: white;
          color: black;
          border-bottom-left-radius: 4px;
          box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .image-content img {
          max-width: 100%;
          border-radius: 12px;
          display: block;
        }
        .status-content {
          display: flex;
          align-items: center;
          gap: 8px;
          font-style: italic;
          color: #65676b;
          font-size: 13px;
        }
        .message-time {
          font-size: 10px;
          margin-top: 4px;
          opacity: 0.7;
          text-align: right;
        }
        .user .message-time {
          color: rgba(255,255,255,0.8);
        }
        .msg-speak-btn {
          background: none;
          border: none;
          margin-left: 8px;
          color: #0084ff;
          cursor: pointer;
        }
        .chat-input-area {
          display: flex;
          align-items: center;
          padding: 10px;
          background: white;
          gap: 10px;
          border-top: 1px solid #eee;
        }
        .input-wrapper {
          flex: 1;
          display: flex;
          align-items: center;
          background: #f0f2f5;
          border-radius: 20px;
          padding: 5px 15px;
        }
        .input-wrapper input {
          flex: 1;
          background: none;
          border: none;
          padding: 8px 0;
          outline: none;
          font-size: 15px;
        }
        .action-btn, .send-btn {
          background: none;
          border: none;
          color: #0084ff;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .send-btn:disabled {
          color: #bcc0c4;
        }
        .voice-btn {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #0084ff;
          color: white;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          position: relative;
        }
        .voice-btn.recording {
          background: #fa3e3e;
          transform: scale(1.2);
        }
        .recording-ring {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          border: 2px solid #fa3e3e;
          animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          100% { transform: scale(2); opacity: 0; }
        }
        .typing-indicator {
          display: flex;
          gap: 4px;
        }
        .typing-indicator span {
          width: 6px;
          height: 6px;
          background: #90949c;
          border-radius: 50%;
          animation: bounce 1s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        .camera-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 100;
          background: black;
          display: flex;
          flex-direction: column;
        }
        .camera-header {
          padding: 15px;
          background: rgba(0,0,0,0.5);
          z-index: 110;
        }
        .close-btn {
          background: none;
          border: none;
          color: white;
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 16px;
        }
      `}</style>
    </div>
  );
};

export default UnifiedChatPage;
