import React, { useCallback, useRef, useEffect, useState } from 'react';
import { X, Check, Image as ImageIcon, Upload } from 'lucide-react';

const CAMERA_COPY = {
  vi: {
    unsupported: 'Trình duyệt không mở được camera ở chế độ hiện tại. Hãy dùng kết nối an toàn hoặc tải ảnh lên.',
    denied: 'Bạn đã từ chối quyền truy cập camera. Hãy cấp quyền trong trình duyệt hoặc dùng nút tải ảnh lên.',
    unavailable: 'Không mở được camera. Hãy thử lại hoặc tải ảnh từ máy tính.',
    captureFailed: 'Không thể chụp ảnh. Hãy thử lại hoặc tải ảnh lên.',
    retry: 'Thử lại',
    upload: 'Tải ảnh lên',
    retake: 'Chụp lại',
    usePhoto: 'Sử dụng'
  },
  en: {
    unsupported: 'Camera access is not available in this browser mode. Use a secure connection or upload a photo instead.',
    denied: 'Camera permission was denied. Allow camera access in the browser or upload a photo instead.',
    unavailable: 'Could not open the camera. Try again or upload a photo from your computer.',
    captureFailed: 'Could not capture the photo. Try again or upload a photo.',
    retry: 'Retry',
    upload: 'Upload photo',
    retake: 'Retake',
    usePhoto: 'Use photo'
  }
};

const CameraScanner = ({ onCapture, language = 'vi', onError }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const streamRef = useRef(null);
  const onErrorRef = useRef(onError);
  const [photo, setPhoto] = useState(null);
  const [error, setError] = useState('');
  const copy = CAMERA_COPY[language] || CAMERA_COPY.vi;

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  // Xây dựng màn hình chụp ảnh: mở camera
  const startCamera = useCallback(async () => {
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("camera_unsupported");
      }
      
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });
      
      streamRef.current = mediaStream;
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setError('');
    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError(copy.denied);
        onErrorRef.current?.('camera_denied');
      } else if (err.message === 'camera_unsupported') {
        setError(copy.unsupported);
        onErrorRef.current?.('camera_unsupported');
      } else {
        setError(copy.unavailable);
        onErrorRef.current?.('camera_unavailable');
      }
    }
  }, [copy.denied, copy.unavailable, copy.unsupported]);

  useEffect(() => {
    startCamera();
    return () => {
      const activeStream = streamRef.current;
      if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    };
  }, [startCamera]);

  // Nút chụp: lấy ảnh từ luồng video hiện tại
  const takePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Limit resolution for capture to avoid massive base64 strings
    const MAX_CAPTURE_WIDTH = 1280;
    const MAX_CAPTURE_HEIGHT = 1280;
    
    let width = video.videoWidth;
    let height = video.videoHeight;

    if (width > height) {
      if (width > MAX_CAPTURE_WIDTH) {
        height = Math.round((height * MAX_CAPTURE_WIDTH) / width);
        width = MAX_CAPTURE_WIDTH;
      }
    } else {
      if (height > MAX_CAPTURE_HEIGHT) {
        width = Math.round((width * MAX_CAPTURE_HEIGHT) / height);
        height = MAX_CAPTURE_HEIGHT;
      }
    }

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    try {
      ctx.drawImage(video, 0, 0, width, height);
      // Reduce quality to 0.8 to save space while keeping enough detail for AI
      const imageData = canvas.toDataURL('image/jpeg', 0.8);
      setPhoto(imageData);
    } catch {
      setError(copy.captureFailed);
      onErrorRef.current?.('camera_capture_failed');
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setPhoto(event.target.result);
    };
    reader.readAsDataURL(file);
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const retakePhoto = () => {
    setPhoto(null);
    // Có thể cần khởi động lại camera nếu nó đã bị dừng
    startCamera();
  };

  const confirmPhoto = () => {
    if (photo) {
      onCapture(photo);
    }
  };

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative', backgroundColor: '#000' }}>

      {/* Hidden Canvas for capturing */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      {/* Hidden Input for file upload fallback */}
      <input 
        type="file" 
        accept="image/*" 
        capture="environment" 
        ref={fileInputRef} 
        style={{ display: 'none' }} 
        onChange={handleFileUpload} 
      />

      {!photo ? (
        // Camera View
        <>
          {/* Preview ảnh trực tiếp từ camera */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />

          {error && (
            <div style={{ position: 'absolute', top: '40%', left: 0, right: 0, textAlign: 'center', color: 'white', padding: 20, zIndex: 10 }}>
              <p style={{ backgroundColor: 'rgba(0,0,0,0.7)', padding: '10px', borderRadius: '8px', display: 'inline-block' }}>{error}</p>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: 15 }}>
                <button onClick={startCamera} style={{ padding: '10px 20px', backgroundColor: '#555', borderRadius: 8, color: 'white', border: 'none' }}>
                  {copy.retry}
                </button>
                <button onClick={triggerFileInput} style={{ padding: '10px 20px', backgroundColor: 'var(--primary-color)', borderRadius: 8, color: 'white', border: 'none', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Upload size={18} /> {copy.upload}
                </button>
              </div>
            </div>
          )}

          {/* UI Overlay */}
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none' }}>
            {/* Guide frame */}
            <div style={{
              position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
              width: '80%', height: '50%', border: '2px solid rgba(255,255,255,0.4)', borderRadius: 20,
              boxShadow: '0 0 0 4000px rgba(0,0,0,0.5)' // Darkens the rest of the screen
            }} />
          </div>

          {/* Controls Bottom Bar */}
          <div style={{
            position: 'absolute', bottom: 60, left: 0, right: 0,
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            zIndex: 10
          }}>
            {/* Nút upload ảnh bên trái nếu không có lỗi */}
            {!error && (
              <button 
                onClick={triggerFileInput}
                style={{ position: 'absolute', left: 40, color: 'white', background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
              >
                <div style={{ width: 44, height: 44, borderRadius: 22, backgroundColor: 'rgba(255,255,255,0.2)', display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 5 }}>
                  <ImageIcon size={24} />
                </div>
              </button>
            )}

            {/* Nút chụp ở giữa */}
            <button
              onClick={takePhoto}
              disabled={!!error}
              style={{
                width: 72, height: 72, borderRadius: 36,
                backgroundColor: 'rgba(255,255,255,0.3)',
                display: 'flex', justifyContent: 'center', alignItems: 'center',
                border: '4px solid white',
                opacity: error ? 0.5 : 1
              }}
            >
              <div style={{ width: 54, height: 54, borderRadius: 27, backgroundColor: error ? '#ccc' : 'white' }} />
            </button>
          </div>
        </>
      ) : (
        // Preview View
        <div className="fade-in" style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: '#000' }}>
          <div style={{ flex: 1, position: 'relative', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {/* Preview ảnh sau khi đã chụp */}
            <img
              src={photo}
              alt="Preview"
              style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
            />
          </div>

          <div style={{
            height: '120px', backgroundColor: 'rgba(30, 30, 30, 0.9)',
            display: 'flex', justifyContent: 'space-around', alignItems: 'center',
            padding: '10px 20px',
            borderTop: '1px solid rgba(255,255,255,0.1)'
          }}>
            <button onClick={retakePhoto} style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', color: '#fff', cursor: 'pointer' }}>
              <div style={{ width: 50, height: 50, borderRadius: 25, backgroundColor: 'rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 5 }}>
                <X size={24} />
              </div>
              <span style={{ fontSize: 12 }}>{copy.retake}</span>
            </button>

            <button onClick={confirmPhoto} style={{ background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', color: '#3b82f6', cursor: 'pointer' }}>
              <div style={{ width: 64, height: 64, borderRadius: 32, backgroundColor: 'rgba(59, 130, 246, 0.2)', display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 5, border: '2px solid #3b82f6' }}>
                <Check size={36} />
              </div>
              <span style={{ fontSize: 14, fontWeight: 'bold' }}>{copy.usePhoto}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraScanner;
