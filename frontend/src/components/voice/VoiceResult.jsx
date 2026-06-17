import React, { useEffect, useState } from 'react';
import { pauseTTS, playTTS, resumeTTS, stopTTS } from '../../services/apiService';

const VoiceResult = ({ textResponse, userTranscript, language, onAskAgain }) => {
  const [speechState, setSpeechState] = useState('idle');

  useEffect(() => {
    return () => stopTTS();
  }, []);

  const handlePlayPause = () => {
    if (!textResponse) return;
    if (speechState === 'playing') {
      if (pauseTTS()) {
        setSpeechState('paused');
      }
      return;
    }
    if (speechState === 'paused') {
      if (resumeTTS()) {
        setSpeechState('playing');
      } else {
        stopTTS();
        setSpeechState('playing');
        playTTS(textResponse, language, () => setSpeechState('idle'));
      }
      return;
    }
    setSpeechState('playing');
    playTTS(textResponse, language, () => setSpeechState('idle'));
  };

  const handleStop = () => {
    stopTTS();
    setSpeechState('idle');
  };

  return (
    <div className="voice-result fade-in">
      <div className="voice-text-stack">
        <div className="transcript-card glass-panel">
          <div className="transcript-label">
            {language === 'vi' ? 'Ban vua noi' : 'You said'}
          </div>
          <div className="transcript-text">
            {userTranscript || (language === 'vi' ? 'Chua nhan duoc noi dung' : 'No transcript yet')}
          </div>
        </div>

        <div className="result-card glass-panel">
          <div className="result-header">
            <span className="bot-icon">🤖</span>
            <h3>AI Tour Guide</h3>
          </div>
          <div className="result-text">
            {textResponse || (language === 'vi' ? 'Day la cau tra loi cua AI' : 'Here is the AI response')}
          </div>
        </div>
      </div>

      <div className="audio-player glass-panel">
        <div className="player-controls">
          <button className="control-btn play-btn" onClick={handlePlayPause} disabled={!textResponse}>
            {speechState === 'playing' ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16"></rect>
                <rect x="14" y="4" width="4" height="16"></rect>
              </svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
            )}
          </button>
          <button className="control-btn" onClick={handleStop} disabled={speechState === 'idle'}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <rect x="5" y="5" width="14" height="14" rx="2" />
            </svg>
          </button>
        </div>
      </div>

      <button className="ask-again-btn primary-btn" onClick={onAskAgain}>
        <span className="mic-icon-small">🎤</span>
        {language === 'vi' ? 'Hỏi lại' : 'Ask again'}
      </button>
    </div>
  );
};

export default VoiceResult;
