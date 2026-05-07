import React, { useState } from 'react';
import CameraScanner from './components/CameraScanner';
import ScanningLoader from './components/ScanningLoader';
import ResultView from './components/ResultView';
import ErrorPopup from './components/ErrorPopup';
import { compressImage } from './utils/imageUtils';
import { recognizeArtifactAPI } from './services/apiService';

function App() {
  const [appState, setAppState] = useState('camera'); // 'camera', 'scanning', 'result'
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState(null); // { type: 'network' | 'blur', message: string }
  const [mockMode, setMockMode] = useState('success'); // 'success', 'blur', 'network'

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

      // Gửi lên API Gateway (giả lập)
      const response = await recognizeArtifactAPI(
        compressedBase64,
        mockMode === 'success' ? null : mockMode
      );

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

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>

      {/* Dev Tools / Mock Controls */}
      {appState === 'camera' && (
        <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 50, display: 'flex', gap: 5 }}>
          <button
            onClick={() => setMockMode('success')}
            style={{ padding: '5px 10px', fontSize: 12, backgroundColor: mockMode === 'success' ? 'green' : '#333', borderRadius: 4, color: 'white' }}
          >Thành công</button>
          <button
            onClick={() => setMockMode('blur')}
            style={{ padding: '5px 10px', fontSize: 12, backgroundColor: mockMode === 'blur' ? 'orange' : '#333', borderRadius: 4, color: 'white' }}
          >Lỗi mờ</button>
          <button
            onClick={() => setMockMode('network')}
            style={{ padding: '5px 10px', fontSize: 12, backgroundColor: mockMode === 'network' ? 'red' : '#333', borderRadius: 4, color: 'white' }}
          >Mất mạng</button>
        </div>
      )}

      {/* Main Views */}
      {appState === 'camera' && <CameraScanner onCapture={handleCapture} />}

      {appState === 'scanning' && <ScanningLoader />}

      {appState === 'result' && resultData && (
        <ResultView data={resultData} onBack={resetToCamera} />
      )}

      {/* Error Popup (Phục vụ cho Mục 5 và Mục 6) */}
      {error && (
        <ErrorPopup
          errorType={error.type}
          message={error.message}
          onRetry={resetToCamera}
          onCancel={resetToCamera}
        />
      )}

    </div>
  );
}

export default App;
