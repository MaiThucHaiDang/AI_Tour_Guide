import React, { useEffect, useRef } from 'react';

const VoiceRecorder = ({ 
  isRecording, 
  startRecording, 
  stopRecording, 
  duration, 
  analyserNode, 
  language,
  onSimulate
}) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    if (isRecording && analyserNode && canvasRef.current) {
      const canvas = canvasRef.current;
      const canvasCtx = canvas.getContext('2d');
      const bufferLength = analyserNode.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const draw = () => {
        animationRef.current = requestAnimationFrame(draw);
        analyserNode.getByteTimeDomainData(dataArray);

        canvasCtx.fillStyle = 'rgba(0, 0, 0, 0)';
        canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

        canvasCtx.lineWidth = 2;
        canvasCtx.strokeStyle = '#a855f7'; // Purple accent

        canvasCtx.beginPath();
        const sliceWidth = (canvas.width * 1.0) / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * canvas.height) / 2;

          if (i === 0) {
            canvasCtx.moveTo(x, y);
          } else {
            canvasCtx.lineTo(x, y);
          }
          x += sliceWidth;
        }

        canvasCtx.lineTo(canvas.width, canvas.height / 2);
        canvasCtx.stroke();
      };

      draw();
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, analyserNode]);

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  // Bấm 1 lần để ghi, bấm 1 lần để dừng (toggle)
  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="voice-recorder fade-in">
      <div className="prompt-text">
        {language === 'vi' ? 'Hãy hỏi tôi về di tích' : 'Ask me about monuments'}
      </div>

      <div className="visualizer-container">
        {isRecording ? (
          <canvas ref={canvasRef} width="300" height="100" className="waveform-canvas" />
        ) : (
          <div className="visualizer-placeholder" style={{ height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'var(--text-secondary)' }}>
              {language === 'vi' ? '≋≋ Sẵn sàng ≋≋' : '≋≋ Ready ≋≋'}
            </span>
          </div>
        )}
      </div>

      <div className="mic-controls">
        <button 
          className={`mic-button ${isRecording ? 'recording' : 'idle'}`}
          onClick={handleMicClick}
        >
          <div className="mic-icon">
            {isRecording ? (
              /* Icon Stop (hình vuông) khi đang ghi */
              <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                <rect x="5" y="5" width="14" height="14" rx="2" />
              </svg>
            ) : (
              /* Icon Mic khi idle */
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
              </svg>
            )}
          </div>
        </button>
        
        <div className="recording-hint">
          {isRecording 
            ? (language === 'vi' ? 'Bấm để dừng' : 'Tap to stop') 
            : (language === 'vi' ? 'Bấm để ghi âm' : 'Tap to record')
          }
        </div>
        
        <div className="duration-display">
          {formatDuration(duration)} / 01:00
        </div>
      </div>
    </div>
  );
};

export default VoiceRecorder;
