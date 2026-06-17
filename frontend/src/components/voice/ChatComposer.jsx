import React from 'react';
import { Camera, Image as ImageIcon, Mic, Send, X } from 'lucide-react';

const ChatComposer = ({
  inputText,
  setInputText,
  pendingImage,
  setPendingImage,
  isRecording,
  recordDuration,
  isProcessing,
  copy,
  handleSendText,
  startRecording,
  stopRecording,
  setShowCamera,
  fileInputRef,
  handleFileUpload
}) => {
  const formatDuration = (seconds) => {
    if (isNaN(seconds) || seconds === null || seconds === undefined) return '00:00';
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  return (
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
          <button onClick={stopRecording} className="stop-rec-btn">
            <Mic size={18} />
          </button>
        </div>
      ) : (
        <div className="composer-row">
          <button onClick={() => setShowCamera(true)} aria-label={copy.camera} className="composer-action-btn">
            <Camera size={20} />
          </button>
          <button onClick={() => fileInputRef.current?.click()} aria-label={copy.upload} className="composer-action-btn">
            <ImageIcon size={20} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <input
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') handleSendText();
            }}
            placeholder={copy.askPlaceholder}
            className="composer-text-input"
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
  );
};

export default ChatComposer;
