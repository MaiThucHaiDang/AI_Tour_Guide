import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Camera, Loader2, RotateCcw, Save, X } from 'lucide-react';
import { composePhotoBoothImage, optimizePhotoBoothImage, preparePhotoBoothFrame } from '../../utils/photoBoothCanvas';
import { getPhotoBoothCameraStream, schedulePhotoBoothCameraRelease } from '../../utils/photoBoothCamera';

const PhotoBoothModal = ({
  frame,
  artifact,
  language = 'vi',
  mode = 'checkin',
  onClose,
  onSave
}) => {
  const isVi = language === 'vi';
  const videoRef = useRef(null);
  const [cameraError, setCameraError] = useState('');
  const [frameError, setFrameError] = useState('');
  const [capturedImage, setCapturedImage] = useState('');
  const [isCapturing, setIsCapturing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isFramePreparing, setIsFramePreparing] = useState(false);
  const [previewFrame, setPreviewFrame] = useState(null);

  const title = useMemo(() => {
    if (mode === 'cover') {
      return isVi ? 'Chụp ảnh bìa chuyến đi' : 'Capture trip cover';
    }
    const name = isVi
      ? artifact?.name_vi || artifact?.nameVi || artifact?.name
      : artifact?.name_en || artifact?.nameEn || artifact?.name;
    return name || (isVi ? 'Check-in ảnh' : 'Photo check-in');
  }, [artifact, isVi, mode]);

  const attachStreamToVideo = useCallback(async (stream) => {
    if (!videoRef.current) return;
    if (videoRef.current.srcObject !== stream) {
      videoRef.current.srcObject = stream;
    }
    await videoRef.current.play();
  }, []);

  const startCamera = useCallback(async () => {
    try {
      setCameraError('');
      const stream = await getPhotoBoothCameraStream();
      await attachStreamToVideo(stream);
      return stream;
    } catch (error) {
      console.error('Photo booth camera failed:', error);
      setCameraError(isVi
        ? 'Không mở được camera. Hãy kiểm tra quyền truy cập camera của trình duyệt.'
        : 'Camera could not be opened. Check the browser camera permission.');
      return null;
    }
  }, [attachStreamToVideo, isVi]);

  useEffect(() => {
    startCamera();

    return () => {
      schedulePhotoBoothCameraRelease();
    };
  }, [startCamera]);

  useEffect(() => {
    let mounted = true;
    setPreviewFrame(null);
    setFrameError('');
    if (!frame?.src) return () => {};

    setIsFramePreparing(true);
    preparePhotoBoothFrame(frame.src)
      .then((result) => {
        if (mounted) setPreviewFrame(result);
      })
      .catch((error) => {
        console.error('Photo booth frame preparation failed:', error);
        if (mounted) {
          setFrameError(isVi
            ? 'Khung ảnh không có vùng đen hợp lệ để thay bằng camera.'
            : 'This frame does not contain a valid black camera area.');
        }
      })
      .finally(() => {
        if (mounted) setIsFramePreparing(false);
      });

    return () => {
      mounted = false;
    };
  }, [frame?.src, isVi]);

  const handleCapture = async () => {
    if (!frame?.src || !videoRef.current || frameError || cameraError) return;
    try {
      setIsCapturing(true);
      setFrameError('');
      const imageBase64 = await composePhotoBoothImage({
        frameSrc: frame.src,
        cameraSource: videoRef.current
      });
      setCapturedImage(imageBase64);
    } catch (error) {
      console.error('Photo booth compose failed:', error);
      setFrameError(isVi
        ? 'Không ghép được ảnh. Khung cần có một vùng đen rõ ràng để thay bằng camera.'
        : 'Could not compose the photo. The frame needs a clear black camera area.');
    } finally {
      setIsCapturing(false);
    }
  };

  const handleRetake = async () => {
    setCapturedImage('');
    await startCamera();
  };

  const handleSave = async () => {
    if (!capturedImage || isSaving) return;
    try {
      setIsSaving(true);
      const albumImage = await optimizePhotoBoothImage(capturedImage);
      onSave?.({
        imageBase64: albumImage || capturedImage,
        frame,
        artifact,
        mode
      });
    } catch (error) {
      console.warn('Photo booth image optimization failed, saving original image:', error);
      onSave?.({
        imageBase64: capturedImage,
        frame,
        artifact,
        mode
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="photo-booth-overlay" role="dialog" aria-modal="true">
      <section className="photo-booth-modal">
        <header className="photo-booth-header">
          <div>
            <span>{mode === 'cover' ? (isVi ? 'Ảnh bìa' : 'Cover') : (isVi ? 'Photo booth' : 'Photo booth')}</span>
            <h2>{title}</h2>
          </div>
          <button type="button" onClick={onClose} aria-label={isVi ? 'Đóng' : 'Close'}>
            <X size={20} />
          </button>
        </header>

        <main className="photo-booth-stage">
          <div
            className="photo-booth-preview"
            style={previewFrame ? { '--frame-ratio': previewFrame.width / previewFrame.height } : undefined}
          >
            <div className="photo-booth-live">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                onCanPlay={() => {
                  videoRef.current?.play().catch(() => {});
                }}
                style={previewFrame ? {
                    left: `${(previewFrame.maskBounds.x / previewFrame.width) * 100}%`,
                    top: `${(previewFrame.maskBounds.y / previewFrame.height) * 100}%`,
                    width: `${(previewFrame.maskBounds.width / previewFrame.width) * 100}%`,
                    height: `${(previewFrame.maskBounds.height / previewFrame.height) * 100}%`
                  } : {
                    inset: 0,
                    width: '100%',
                    height: '100%'
                  }}
              />
              {previewFrame?.overlaySrc && (
                <img src={previewFrame.overlaySrc} alt="" aria-hidden="true" />
              )}
            </div>
            {capturedImage && (
              <img className="photo-booth-result" src={capturedImage} alt={isVi ? 'Ảnh check-in đã ghép' : 'Composed check-in'} />
            )}
          </div>
          {isFramePreparing && (
            <p className="photo-booth-status">
              {isVi ? 'Đang chuẩn bị khung ảnh...' : 'Preparing photo frame...'}
            </p>
          )}
          {cameraError && <p className="photo-booth-error">{cameraError}</p>}
          {frameError && <p className="photo-booth-error">{frameError}</p>}
        </main>

        <footer className="photo-booth-actions">
          {capturedImage ? (
            <>
              <button type="button" className="photo-booth-secondary" onClick={handleRetake}>
                <RotateCcw size={17} />
                {isVi ? 'Chụp lại' : 'Retake'}
              </button>
              <button type="button" className="photo-booth-primary" onClick={handleSave} disabled={isSaving}>
                {isSaving ? <Loader2 className="spin" size={17} /> : <Save size={17} />}
                {isSaving ? (isVi ? 'Đang lưu...' : 'Saving...') : mode === 'cover'
                  ? (isVi ? 'Lưu ảnh bìa' : 'Save cover')
                  : (isVi ? 'Lưu check-in' : 'Save check-in')}
              </button>
            </>
          ) : (
            <button
              type="button"
              className="photo-booth-primary"
              onClick={handleCapture}
              disabled={isCapturing || Boolean(cameraError) || Boolean(frameError)}
            >
              {isCapturing ? <Loader2 className="spin" size={17} /> : <Camera size={17} />}
              {isCapturing ? (isVi ? 'Đang ghép...' : 'Composing...') : (isVi ? 'Chụp ảnh' : 'Capture')}
            </button>
          )}
        </footer>
      </section>
    </div>
  );
};

export default PhotoBoothModal;
