import React from 'react';

const VoiceProcessing = ({ language }) => {
  return (
    <div className="voice-processing fade-in">
      <div className="processing-animation">
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
        <div className="wave-bar"></div>
      </div>
      <div className="processing-text">
        {language === 'vi' ? 'AI đang xử lý...' : 'AI is processing...'}
      </div>
    </div>
  );
};

export default VoiceProcessing;
