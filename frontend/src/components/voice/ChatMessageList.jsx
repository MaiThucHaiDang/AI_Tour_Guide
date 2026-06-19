import React from 'react';
import { Loader2, Pause, Play, Volume2, ThumbsUp, ThumbsDown, X, ChevronDown, Sparkles } from 'lucide-react';

const ChatMessageList = ({
  messages,
  isProcessing,
  language,
  copy,
  activeAudioMsgId,
  speechState,
  showJumpToLatest,
  handleSpeakMessage,
  handleFeedback,
  handleMessageListScroll,
  handleJumpToLatest,
  handleStopAudio,
  handleSelectHistoryAudio,
  messageListRef,
  messagesEndRef
}) => {
  const isVi = language === 'vi';

  return (
    <div className="chat-message-list-container">
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
                        aria-label={isCurrentPlaying ? (isVi ? 'Tạm dừng' : 'Pause') : isCurrentPaused ? (isVi ? 'Phát tiếp' : 'Resume') : copy.listen}
                        title={isCurrentPlaying ? (isVi ? 'Tạm dừng' : 'Pause') : isCurrentPaused ? (isVi ? 'Phát tiếp' : 'Resume') : copy.listen}
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

      {/* Mini floating audio player */}
      {activeAudioMsgId && (() => {
        const activeMsg = messages.find(m => m.id === activeAudioMsgId) || {};
        const historyItems = messages
          .filter(m => m.role === 'ai' && m.type === 'text' && !m.isStreaming)
          .slice(-3);

        const displayTitle = activeMsg.content 
          ? (activeMsg.content.length > 24 ? activeMsg.content.slice(0, 24) + '...' : activeMsg.content)
          : (isVi ? 'Đang đọc' : 'Reading');

        return (
          <div className="bottom-audio-player">
            <div className="audio-player-layout">
              <div className="audio-player-meta">
                <div className={`audio-wave-icon ${speechState === 'playing' ? 'wave-playing' : ''}`}>
                  <Volume2 size={16} />
                </div>
                <div className="audio-meta-text">
                  <strong>{displayTitle}</strong>
                  <span>{isVi ? 'Đang đọc' : 'Reading'}</span>
                </div>
              </div>

              <div className="audio-player-controls-section">
                <div className="audio-playback-buttons">
                  <button 
                    className="play-pause-toggle-btn"
                    onClick={() => handleSpeakMessage(activeMsg)} 
                    title={speechState === 'playing' ? (isVi ? 'Tạm dừng' : 'Pause') : (isVi ? 'Phát' : 'Play')}
                    aria-label={speechState === 'playing' ? 'Pause' : 'Play'}
                  >
                    {speechState === 'playing' ? <Pause size={16} /> : <Play size={16} />}
                  </button>
                  <button onClick={handleStopAudio} className="stop-playback-btn" title={isVi ? 'Dừng phát' : 'Stop'} aria-label="Stop playback">
                    <X size={14} />
                  </button>
                </div>
              </div>
            </div>

            {historyItems.length > 0 && (
              <div className="audio-history-switcher">
                <span className="switcher-label">
                  <Sparkles size={11} />
                  {isVi ? '3 câu thoại gần nhất:' : 'Last 3 narrations:'}
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
    </div>
  );
};

export default React.memo(ChatMessageList, (prevProps, nextProps) => {
  return prevProps.messages === nextProps.messages &&
         prevProps.isProcessing === nextProps.isProcessing &&
         prevProps.language === nextProps.language &&
         prevProps.activeAudioMsgId === nextProps.activeAudioMsgId &&
         prevProps.speechState === nextProps.speechState &&
         prevProps.showJumpToLatest === nextProps.showJumpToLatest;
});
