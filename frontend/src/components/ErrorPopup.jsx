import React from 'react';
import { AlertCircle, WifiOff } from 'lucide-react';

const ErrorPopup = ({ errorType, message, onRetry, onCancel }) => {
  const isNetwork = errorType === 'network';
  
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
          backgroundColor: isNetwork ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          margin: '0 auto 20px', color: isNetwork ? 'var(--error-color)' : '#f59e0b'
        }}>
          {isNetwork ? <WifiOff size={32} /> : <AlertCircle size={32} />}
        </div>

        <h3 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 10 }}>
          {isNetwork ? 'Mất kết nối' : 'Không nhận diện được'}
        </h3>
        
        <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginBottom: 25, lineHeight: 1.5 }}>
          {message || (isNetwork ? 'Chà, mất mạng rồi! Bạn kiểm tra lại wifi hoặc 4G nhé.' : 'Góc này hơi tối hoặc bị mờ, bạn chụp lại rõ hơn giúp mình nhé!')}
        </p>

        <div style={{ display: 'flex', gap: 15 }}>
          <button 
            onClick={onCancel}
            style={{ 
              flex: 1, padding: '14px 0', borderRadius: 12, 
              backgroundColor: '#333', fontWeight: 600 
            }}
          >
            Hủy
          </button>
          <button 
            onClick={onRetry}
            style={{ 
              flex: 1, padding: '14px 0', borderRadius: 12, 
              backgroundColor: 'var(--primary-color)', fontWeight: 600, color: 'white'
            }}
          >
            Chụp lại
          </button>
        </div>

      </div>
    </div>
  );
};

export default ErrorPopup;
