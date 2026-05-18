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
          {language === 'vi' ? 'Xin chào, bạn muốn làm gì?' : 'Hello, what would you like to do?'}
        </h2>
        
        <div className="feature-cards-container">
          {/* Feature 1: Camera Scanner */}
          <div 
            className="feature-card glass-panel pop-in" 
            style={{ animationDelay: '0.1s' }}
            onClick={() => onSelectFeature('camera')}
          >
            <div className="feature-icon-wrapper camera-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
            </div>
            <h3 className="feature-title">
              {language === 'vi' ? 'Nhận diện hiện vật' : 'Scan Artifact'}
            </h3>
            <p className="feature-desc">
              {language === 'vi' ? 'Quét bằng camera để xem thông tin chi tiết.' : 'Use camera to scan and get detailed info.'}
            </p>
          </div>

          {/* Feature 2: AI Chat */}
          <div 
            className="feature-card glass-panel pop-in" 
            style={{ animationDelay: '0.2s' }}
            onClick={() => onSelectFeature('chat')}
          >
            <div className="feature-icon-wrapper chat-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <h3 className="feature-title">
              {language === 'vi' ? 'Hỏi đáp với AI' : 'Chat with AI'}
            </h3>
            <p className="feature-desc">
              {language === 'vi' ? 'Trò chuyện và hỏi thêm thông tin du lịch.' : 'Chat and ask for more travel information.'}
            </p>
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
