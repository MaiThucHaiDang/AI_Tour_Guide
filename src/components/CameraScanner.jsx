import React, { useRef, useEffect, useState } from 'react';
import { Camera, X, Check, Image as ImageIcon } from 'lucide-react';

const CameraScanner = ({ onCapture }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [photo, setPhoto] = useState(null);
  const [error, setError] = useState('');

  // Xây dựng màn hình chụp ảnh: mở camera
  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' } // Prefer back camera
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setError('');
    } catch (err) {
      console.error("Camera error:", err);
      setError('Không thể truy cập camera. Vui lòng cấp quyền.');
    }
  };

  useEffect(() => {
    startCamera();
    return () => {
      // Cleanup stream when unmounting
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Nút chụp: lấy ảnh từ luồng video hiện tại
  const takePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Get full quality image, compression will happen in the pipeline
    const imageData = canvas.toDataURL('image/jpeg', 1.0);
    setPhoto(imageData);
  };

  const retakePhoto = () => {
    setPhoto(null);
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
            <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, textAlign: 'center', color: 'white', padding: 20 }}>
              <p>{error}</p>
              <button onClick={startCamera} style={{ marginTop: 10, padding: '10px 20px', backgroundColor: 'var(--primary-color)', borderRadius: 8, color: 'white' }}>
                Thử lại
              </button>
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

          {/* Capture Button */}
          <div style={{
            position: 'absolute', bottom: 40, left: 0, right: 0,
            display: 'flex', justifyContent: 'center', alignItems: 'center'
          }}>
            {/* Nút chụp */}
            <button
              onClick={takePhoto}
              style={{
                width: 72, height: 72, borderRadius: 36,
                backgroundColor: 'rgba(255,255,255,0.3)',
                display: 'flex', justifyContent: 'center', alignItems: 'center',
                border: '4px solid white'
              }}
            >
              <div style={{ width: 54, height: 54, borderRadius: 27, backgroundColor: 'white' }} />
            </button>
          </div>
        </>
      ) : (
        // Preview View
        <div className="fade-in" style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            {/* Preview ảnh sau khi đã chụp */}
            <img
              src={photo}
              alt="Preview"
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </div>

          <div style={{
            height: 100, backgroundColor: '#1e1e1e',
            display: 'flex', justifyContent: 'space-around', alignItems: 'center',
            padding: '0 20px'
          }}>
            <button onClick={retakePhoto} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: '#a0a0a0' }}>
              <div style={{ width: 50, height: 50, borderRadius: 25, backgroundColor: '#333', display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 5 }}>
                <X size={24} />
              </div>
              <span style={{ fontSize: 12 }}>Chụp lại</span>
            </button>

            <button onClick={confirmPhoto} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: 'var(--primary-color)' }}>
              <div style={{ width: 60, height: 60, borderRadius: 30, backgroundColor: 'rgba(59, 130, 246, 0.2)', display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 5 }}>
                <Check size={32} />
              </div>
              <span style={{ fontSize: 14, fontWeight: 'bold' }}>Sử dụng</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraScanner;
