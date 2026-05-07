import React from 'react';
import { ScanFace } from 'lucide-react';

const ScanningLoader = () => {
  return (
    <div className="fade-in" style={{ 
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.85)',
      display: 'flex', flexDirection: 'column',
      justifyContent: 'center', alignItems: 'center',
      zIndex: 100
    }}>
      
      <div style={{ position: 'relative', width: 120, height: 120, marginBottom: 30 }}>
        {/* Animated ring */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          borderRadius: '50%',
          animation: 'pulse-ring 2s infinite'
        }} />
        
        {/* Scanner Icon */}
        <div className="glass-panel flex-center" style={{ width: '100%', height: '100%', borderRadius: '50%' }}>
          <ScanFace size={50} color="var(--primary-color)" />
        </div>

        {/* Scan line effect */}
        <div style={{
          position: 'absolute', left: '20%', right: '20%', height: 2,
          backgroundColor: 'var(--primary-color)',
          boxShadow: '0 0 10px var(--primary-color)',
          animation: 'scan-line 2s linear infinite'
        }} />
      </div>

      <h2 style={{ fontSize: 20, fontWeight: 600, color: 'white', marginBottom: 10 }}>AI Đang Phân Tích</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Vui lòng chờ một chút...</p>
    </div>
  );
};

export default ScanningLoader;
