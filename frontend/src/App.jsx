import React, { useState, useEffect } from 'react';
import HomeScreen from './components/HomeScreen';
import UnifiedChatPage from './components/voice/UnifiedChatPage';

function App() {
  const [appState, setAppState] = useState(() => {
    return new URLSearchParams(window.location.search).get('view') === 'chat' ? 'chat' : 'home';
  });
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('ai_tour_lang') || 'vi';
  });

  useEffect(() => {
    localStorage.setItem('ai_tour_lang', language);
  }, [language]);

  const resetToHome = () => {
    setAppState('home');
  };

  const handleSelectFeature = () => {
    setAppState('chat');
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>

      {/* Main Views */}
      {appState === 'home' && (
        <HomeScreen
          onSelectFeature={handleSelectFeature}
          language={language}
          setLanguage={setLanguage}
        />
      )}

      {appState === 'chat' && (
        <UnifiedChatPage
          onBack={resetToHome}
          language={language}
          setLanguage={setLanguage}
        />
      )}

    </div>
  );
}

export default App;
