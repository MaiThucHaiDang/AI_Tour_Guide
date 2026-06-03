import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Volume2, ArrowLeft } from 'lucide-react';
import { playTTS, stopTTS } from '../services/apiService';

const ResultView = ({ data, onBack }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    setIsPlaying(true);
    playTTS(data.text_response, () => {
      setIsPlaying(false);
    });

    return () => {
      stopTTS();
    };
  }, [data.text_response]);

  // Nhận audio stream từ TTS Service, phát qua loa thiết bị
  const handlePlayAudio = () => {
    if (isPlaying) {
      stopTTS();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      playTTS(data.text_response, () => {
        setIsPlaying(false);
      });
    }
  };

  const handleReplay = () => {
    stopTTS();
    setIsPlaying(true);
    playTTS(data.text_response, () => {
      setIsPlaying(false);
    });
  };

  return (
    <div className="fade-in" style={{ height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-color)' }}>

      {/* Header */}
      <div style={{ padding: '20px', display: 'flex', alignItems: 'center' }}>
        <button onClick={onBack} style={{ padding: '10px', borderRadius: '50%', backgroundColor: 'var(--card-bg)' }}>
          <ArrowLeft size={24} />
        </button>
        <h1 style={{ marginLeft: 15, fontSize: 18, fontWeight: 600 }}>Thông tin nhận diện</h1>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '0 20px 120px' }}>
        {/* Ảnh minh họa cho kết quả nhận diện */}
        <div style={{
          width: '100%', height: 220, borderRadius: 16,
          backgroundColor: '#2a2a2a', marginBottom: 20,
          backgroundImage: 'linear-gradient(45deg, #1e1e1e, #2a2a2a)',
          display: 'flex', justifyContent: 'center', alignItems: 'center'
        }}>
          <img
            src="https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=800&q=80"
            alt="Hue"
            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 16, opacity: 0.8 }}
          />
        </div>

        {/* Content */}
        <div className="glass-panel" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 15 }}>
            <div>
              {/* Nhận kết quả từ backend: hiển thị tên điểm/hiện vật */}
              <h2 style={{ fontSize: 24, fontWeight: 'bold', color: 'var(--primary-color)' }}>{data.artifact_name}</h2>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Mã: {data.artifact_id} • Độ chính xác: {Math.round(data.confidence_score * 100)}%</span>
            </div>

            <div style={{
              backgroundColor: isPlaying ? 'rgba(59, 130, 246, 0.2)' : 'var(--card-bg)',
              padding: '10px', borderRadius: '50%', color: isPlaying ? 'var(--primary-color)' : 'white',
              animation: isPlaying ? 'pulse-ring 2s infinite' : 'none'
            }}>
              <Volume2 size={20} />
            </div>
          </div>

          {/* Nhận kết quả từ backend: nội dung text lên UI */}
          <p style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--text-main)' }}>
            {data.text_response}
          </p>
        </div>
      </div>

      {/* Audio Controls fixed at bottom */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        backgroundColor: 'var(--card-bg)', borderTop: '1px solid #333',
        padding: '20px 30px', display: 'flex', justifyContent: 'center', alignItems: 'center',
        paddingBottom: 'max(20px, env(safe-area-inset-bottom))'
      }}>

        <button onClick={handleReplay} style={{
          width: 50, height: 50, borderRadius: 25,
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          color: 'var(--text-secondary)'
        }}>
          <RotateCcw size={24} />
        </button>

        <button onClick={handlePlayAudio} style={{
          width: 70, height: 70, borderRadius: 35,
          backgroundColor: 'var(--primary-color)',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          margin: '0 30px', color: 'white',
          boxShadow: '0 4px 15px rgba(59, 130, 246, 0.4)'
        }}>
          {isPlaying ? <Pause size={32} /> : <Play size={32} style={{ marginLeft: 4 }} />}
        </button>

      </div>
    </div>
  );
};

export default ResultView;
