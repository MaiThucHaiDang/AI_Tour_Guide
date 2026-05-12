import React from 'react';

const VoiceErrorPopup = ({ errorType, onRetry, onCancel, language = 'vi' }) => {
  let icon = '⚠️';
  let titleVi = 'Lỗi';
  let titleEn = 'Error';
  let descVi = 'Đã có lỗi xảy ra.';
  let descEn = 'An error occurred.';

  switch (errorType) {
    case 'microphone_denied':
      icon = '🔒';
      titleVi = 'Quyền Microphone Bị Từ Chối';
      titleEn = 'Microphone Access Denied';
      descVi = 'Vui lòng cấp quyền microphone trong cài đặt trình duyệt để sử dụng tính năng này.';
      descEn = 'Please allow microphone access in browser settings to use this feature.';
      break;
    case 'network_error':
    case 'TIMEOUT':
      icon = '📡';
      titleVi = 'Mất Kết Nối Mạng';
      titleEn = 'Network Disconnected';
      descVi = 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại kết nối mạng của bạn.';
      descEn = 'Cannot connect to the server. Please check your internet connection.';
      break;
    case 'empty_transcription':
    case 'recording_too_short':
    default:
      icon = '🎙️';
      titleVi = 'Không Nghe Rõ';
      titleEn = "Couldn't Hear Clearly";
      descVi = 'Không nghe rõ, bạn nói lại nhé!';
      descEn = "Couldn't hear clearly, please try again!";
      break;
  }

  return (
    <div className="fade-in" style={{
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(5px)',
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      zIndex: 200, padding: 20
    }}>
      <div className="pop-in glass-panel" style={{
        width: '100%', maxWidth: 340, backgroundColor: 'var(--card-bg)',
        padding: 25, borderRadius: 24, textAlign: 'center'
      }}>

        <div style={{
          width: 64, height: 64, borderRadius: 32,
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          margin: '0 auto 20px', color: 'var(--error-color)'
        }}>
          <span style={{ fontSize: 32 }}>{icon}</span>
        </div>

        <h3 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 10 }}>
          {language === 'vi' ? titleVi : titleEn}
        </h3>

        <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginBottom: 25, lineHeight: 1.5 }}>
          {language === 'vi' ? descVi : descEn}
        </p>

        <div style={{ display: 'flex', gap: 15 }}>
          <button
            onClick={onCancel}
            style={{
              flex: 1, padding: '14px 0', borderRadius: 12,
              backgroundColor: '#333', fontWeight: 600, color: 'white'
            }}
          >
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
          {errorType !== 'microphone_denied' && (
            <button
              onClick={onRetry}
              style={{
                flex: 1, padding: '14px 0', borderRadius: 12,
                backgroundColor: 'var(--primary-color)', fontWeight: 600, color: 'white'
              }}
            >
              {language === 'vi' ? 'Thử lại' : 'Retry'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceErrorPopup;
