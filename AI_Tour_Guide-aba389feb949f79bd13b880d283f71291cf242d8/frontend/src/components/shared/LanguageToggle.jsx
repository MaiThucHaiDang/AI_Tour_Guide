import React from 'react';

const LanguageToggle = ({ language, setLanguage }) => {
  return (
    <div className="language-toggle glass-panel">
      <button 
        className={`lang-btn ${language === 'vi' ? 'active' : ''}`}
        onClick={() => setLanguage('vi')}
      >
        VI
      </button>
      <button 
        className={`lang-btn ${language === 'en' ? 'active' : ''}`}
        onClick={() => setLanguage('en')}
      >
        EN
      </button>
    </div>
  );
};

export default LanguageToggle;
