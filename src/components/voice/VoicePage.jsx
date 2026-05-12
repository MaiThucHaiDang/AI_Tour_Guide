import React, { useState, useEffect, useRef } from 'react';
import VoiceRecorder from './VoiceRecorder';
import VoiceProcessing from './VoiceProcessing';
import VoiceResult from './VoiceResult';
import VoiceErrorPopup from './VoiceErrorPopup';
import LanguageToggle from '../shared/LanguageToggle';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import { voiceChatAPI } from '../../services/apiService';

const VoicePage = ({ onBack, language, setLanguage }) => {
  const [voiceState, setVoiceState] = useState('idle'); // 'idle', 'recording', 'processing', 'result', 'error'
  const [apiError, setApiError] = useState(null);
  const [apiErrorDetail, setApiErrorDetail] = useState(null);
  const [audioResult, setAudioResult] = useState(null);

  // Guard: chỉ process khi đang thực sự ở state 'recording'
  const voiceStateRef = useRef('idle');
  const abortControllerRef = useRef(null);

  const setVoiceStateSynced = (state) => {
    voiceStateRef.current = state;
    setVoiceState(state);
  };

  const {
    isRecording,
    audioBlob,
    duration,
    durationRef,
    analyserNode,
    startRecording,
    stopRecording,
    resetRecording,
    getFilename,
    error: recorderError
  } = useAudioRecorder();

  // Handle recorder error
  useEffect(() => {
    if (recorderError) {
      setApiError(recorderError);
      setApiErrorDetail(null);
      setVoiceStateSynced('error');
    }
  }, [recorderError]);

  // Handle recording completion -> trigger API call
  // Dùng ref để kiểm tra state chính xác, tránh stale closure
  useEffect(() => {
    if (!audioBlob) return;
    if (voiceStateRef.current !== 'recording') return; // Guard: chỉ xử lý khi đang ghi âm

    const elapsed = durationRef.current;
    console.log('[VoicePage] audioBlob ready, elapsed:', elapsed, 's');

    if (elapsed < 0.5) {
      setApiError('recording_too_short');
      setApiErrorDetail(null);
      setVoiceStateSynced('error');
      return;
    }

    processAudio(audioBlob, language, getFilename());
  }, [audioBlob]);

  const handleStartRecording = () => {
    setVoiceStateSynced('recording');
    resetRecording();
    setAudioResult(null);
    setApiError(null);
    // startRecording is async (getUserMedia) — VoiceRecorder calls it via onClick
    startRecording();
  };

  const handleStopRecording = () => {
    // stopRecording sẽ tự tính duration và tạo audioBlob
    stopRecording();
  };

  const processAudio = async (blob, lang, filename = 'recording.webm') => {
    setVoiceStateSynced('processing');

    abortControllerRef.current = new AbortController();

    try {
      console.log('[VoicePage] Calling voiceChatAPI, lang:', lang, 'file:', filename, 'size:', blob.size);
      const responseBlob = await voiceChatAPI(blob, lang, abortControllerRef.current.signal, filename);

      console.log('[VoicePage] API response received, size:', responseBlob.size);

      // Nếu response quá nhỏ thì có thể là lỗi empty
      if (responseBlob.size < 1000) {
        setApiError('backend_detail');
        setApiErrorDetail('Phan hoi am thanh qua nho. Vui long thu lai.');
        setVoiceStateSynced('error');
      } else {
        setAudioResult(responseBlob);
        setVoiceStateSynced('result');
      }
    } catch (err) {
      console.error('[VoicePage] processAudio error:', err);
      if (err.name === 'AbortError') {
        // Bị hủy có chủ đích (đổi ngôn ngữ), không set error
        return;
      }
      if (err.message === 'TIMEOUT' || err.message === 'NETWORK_ERROR' || err.message?.includes('Failed to fetch')) {
        setApiError('network_error');
        setApiErrorDetail(null);
      } else if (err.message?.includes('Empty transcription')) {
        setApiError('empty_transcription');
        setApiErrorDetail(null);
      } else {
        setApiError('backend_detail');
        setApiErrorDetail(err.message || null);
      }
      setVoiceStateSynced('error');
    }
  };

  // Khi đổi ngôn ngữ trong lúc đang processing, hủy và gọi lại
  useEffect(() => {
    if (voiceStateRef.current === 'processing' && audioBlob) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      processAudio(audioBlob, language, getFilename());
    }
  }, [language]);

  const handleRetry = () => {
    // Reset tất cả state về idle, KHÔNG gọi stopRecording (đã stop rồi)
    setVoiceStateSynced('idle');
    setApiError(null);
    setApiErrorDetail(null);
    setAudioResult(null);
    resetRecording(); // Xóa audioBlob cũ để effect không kích hoạt lại
  };

  const handleCancel = () => {
    setVoiceStateSynced('idle');
    setApiError(null);
    setApiErrorDetail(null);
    setAudioResult(null);
    resetRecording();
  };

  return (
    <div className="voice-page fade-in">
      {/* Header */}
      <div className="voice-header">
        <button className="back-btn" onClick={onBack}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          {language === 'vi' ? 'Quay lại' : 'Back'}
        </button>
        <div className="header-title">
          <span className="icon">🏛️</span> AI Tour
        </div>
        <LanguageToggle language={language} setLanguage={setLanguage} />
      </div>

      {/* Main Content Area */}
      <div className="voice-content">
        {(voiceState === 'idle' || voiceState === 'recording') && (
          <VoiceRecorder
            isRecording={isRecording}
            startRecording={handleStartRecording}
            stopRecording={handleStopRecording}
            duration={duration}
            analyserNode={analyserNode}
            language={language}
          />
        )}

        {voiceState === 'processing' && (
          <VoiceProcessing language={language} />
        )}

        {voiceState === 'result' && (
          <VoiceResult
            audioBlob={audioResult}
            textResponse=""
            language={language}
            onAskAgain={handleRetry}
          />
        )}
      </div>

      {/* Error Popup - nằm TRONG voice-page để overlay đúng */}
      {voiceState === 'error' && (
        <VoiceErrorPopup
          errorType={apiError}
          errorDetail={apiErrorDetail}
          onRetry={handleRetry}
          onCancel={handleCancel}
          language={language}
        />
      )}
    </div>
  );
};

export default VoicePage;
