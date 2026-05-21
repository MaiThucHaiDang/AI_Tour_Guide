import React from 'react';

const HomeScreen = ({ onSelectFeature, language, setLanguage }) => {
  return (
    <div className="home-screen fade-in">
      {/* Header with Logo and Language Toggle */}
      <header className="home-header">
        <div className="logo-container">
          <div className="logo-icon">🏛️</div>
          <h1 className="logo-text">AI Tour Guide</h1>
        </div>
        
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
      </header>

      {/* Main Content - Feature Selection */}
      <main className="home-main">
        <h2 className="welcome-text">
          {language === 'vi' ? 'Chào mừng bạn đến với AI Tour Guide' : 'Welcome to AI Tour Guide'}
        </h2>
        
        <div className="feature-cards-container">
          {/* Unified Feature: AI Assistant */}
          <div 
            className="feature-card glass-panel pop-in" 
            style={{ animationDelay: '0.1s' }}
            onClick={() => onSelectFeature('unified')}
          >
            <div className="feature-icon-wrapper unified-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
                <path d="M12 12L2.7 7.3"></path>
                <path d="M12 12V22"></path>
                <path d="M12 12l9.3 4.7"></path>
                <path d="M22 12A10 10 0 0 0 12 2v10h10z"></path>
              </svg>
            </div>
            <h3 className="feature-title">
              {language === 'vi' ? 'Khám phá cùng AI' : 'Explore with AI'}
            </h3>
            <p className="feature-desc">
              {language === 'vi' 
                ? 'Nhận diện hiện vật và trò chuyện hỏi đáp thông tin du lịch.' 
                : 'Identify artifacts and chat for travel information.'}
            </p>
            <button className="start-btn">
              {language === 'vi' ? 'Bắt đầu ngay' : 'Get Started'}
            </button>
          </div>
        </div>
      </main>

      {/* Decorative background elements */}
      <div className="bg-blob blob-1"></div>
      <div className="bg-blob blob-2"></div>
    </div>
  );
};

export default HomeScreen;
