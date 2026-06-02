import React, { useState, useEffect } from 'react';
import HomeScreen from './components/HomeScreen';
import ExploreDashboard from './components/dashboard/ExploreDashboard';
import MapCalibrate from './components/map/MapCalibrate';

function App() {
  const [appState, setAppState] = useState(() => {
    const view = new URLSearchParams(window.location.search).get('view');
    if (view === 'calibrate') return 'calibrate';
    return view === 'dashboard' ? 'dashboard' : 'home';
  });
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('ai_tour_lang') || 'vi';
  });
  const [selectedLocation, setSelectedLocation] = useState(null);

  useEffect(() => {
    localStorage.setItem('ai_tour_lang', language);
  }, [language]);

  const resetToHome = () => {
    setAppState('home');
    setSelectedLocation(null);
  };

  const handleSelectLocation = (location) => {
    setSelectedLocation(location);
    setAppState('dashboard');
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>

      {/* Main Views */}
      {appState === 'home' && (
        <HomeScreen
          onSelectFeature={(feature, data) => {
            if (feature === 'dashboard' || feature === 'chat' || feature === 'map') {
              handleSelectLocation({ id: 1, name_vi: "Kinh thành Huế (Đại Nội)" });
            }
          }}
          language={language}
          setLanguage={setLanguage}
        />
      )}

      {appState === 'dashboard' && (
        <ExploreDashboard
          onBack={resetToHome}
          language={language}
          setLanguage={setLanguage}
          initialLocation={selectedLocation}
        />
      )}

      {appState === 'calibrate' && (
        <MapCalibrate
          onBack={resetToHome}
          language={language}
        />
      )}

    </div>
  );
}

export default App;
