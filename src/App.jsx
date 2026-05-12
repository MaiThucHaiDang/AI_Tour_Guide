import React, { useState, useEffect } from 'react';
import CameraScanner from './components/CameraScanner';
import ScanningLoader from './components/ScanningLoader';
import ResultView from './components/ResultView';
import ErrorPopup from './components/ErrorPopup';
import HomeScreen from './components/HomeScreen';
import VoicePage from './components/voice/VoicePage';
import { compressImage } from './utils/imageUtils';
import { recognizeArtifactAPI } from './services/apiService';

function App() {
  const [appState, setAppState] = useState('home'); // 'home', 'camera', 'scanning', 'result'
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState(null); // { type: 'network' | 'blur', message: string }
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('ai_tour_lang') || 'vi';
  });

  useEffect(() => {
    localStorage.setItem('ai_tour_lang', language);
  }, [language]);

  const handleCapture = async (photoBase64) => {
    try {
      setAppState('scanning');
      setError(null);

      // Nén ảnh, convert sang base64 (giả sử resize xuống 800px)
      const compressedBase64 = await compressImage(photoBase64, 800, 800, 0.7);

      // Calculate sizes for console just to show it's working
      const originalSize = Math.round((photoBase64.length * 3) / 4 / 1024);
      const compressedSize = Math.round((compressedBase64.length * 3) / 4 / 1024);
      console.log(`Original: ${originalSize}KB, Compressed: ${compressedSize}KB`);

      // Gửi lên API Gateway (Thực tế)
      const response = await recognizeArtifactAPI(compressedBase64, language);

      if (response.status === 'success') {
        setResultData(response.data);
        setAppState('result');
      } else {
        // Xử lý edge case: ảnh tối/mờ -> hiển thị thông báo yêu cầu chụp lại
        setError({
          type: 'blur',
          message: response.message
        });
        setAppState('camera');
      }

    } catch (err) {
      console.error(err);
      // Xử lý mất kết nối: hiển thị thông báo lỗi
      setError({
        type: 'network',
        message: 'Chà, mất mạng rồi! Bạn kiểm tra lại wifi/4G nhé.'
      });
      setAppState('camera');
    }
  };

  const resetToCamera = () => {
    setAppState('camera');
    setResultData(null);
    setError(null);
  };

  const resetToHome = () => {
    setAppState('home');
    setResultData(null);
    setError(null);
  };

  const handleSelectFeature = (feature) => {
    if (feature === 'camera') {
      setAppState('camera');
    } else if (feature === 'chat') {
      setAppState('voice');
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>

      {/* Nút Back về Home khi đang ở Camera */}
      {appState === 'camera' && (
        <button
          onClick={resetToHome}
          style={{ position: 'absolute', top: 20, left: 20, zIndex: 50, background: 'rgba(0,0,0,0.5)', padding: '8px 12px', borderRadius: '8px', color: 'white' }}
        >
          &larr; {language === 'vi' ? 'Quay lại' : 'Back'}
        </button>
      )}

      {/* Main Views */}
      {appState === 'home' && (
        <HomeScreen
          onSelectFeature={handleSelectFeature}
          language={language}
          setLanguage={setLanguage}
        />
      )}

      {appState === 'camera' && <CameraScanner onCapture={handleCapture} />}

      {appState === 'scanning' && <ScanningLoader />}

      {appState === 'result' && resultData && (
        <ResultView data={resultData} onBack={resetToCamera} />
      )}

      {/* Error Popup (Phục vụ cho Mục 5 và Mục 6) */}
      {error && appState !== 'voice' && (
        <ErrorPopup
          errorType={error.type}
          message={error.message}
          onRetry={resetToCamera}
          onCancel={resetToCamera}
        />
      )}

      {appState === 'voice' && (
        <VoicePage
          onBack={resetToHome}
          language={language}
          setLanguage={setLanguage}
        />
      )}

    </div>
  );
}

export default App;
