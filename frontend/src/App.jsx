import React, { useState, useEffect } from 'react';
import HomeScreen from './components/HomeScreen';
import ExploreDashboard from './components/dashboard/ExploreDashboard';
import MapCalibrate from './components/map/MapCalibrate';
import PhonePreview from './components/PhonePreview';

const DEFAULT_TOUR_LOCATION = {
  id: 1,
  name_vi: 'Kinh thành Huế (Đại Nội)',
  name_en: 'Hue Imperial City'
};

const updateViewQuery = (view) => {
  const url = new URL(window.location.href);
  if (view === 'home') {
    url.searchParams.delete('view');
  } else {
    url.searchParams.set('view', view);
  }
  window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
};

function App() {
  const [appState, setAppState] = useState(() => {
    const view = new URLSearchParams(window.location.search).get('view');
    if (view === 'calibrate') return 'calibrate';
    if (view === 'phone') return 'phone';
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
    updateViewQuery('home');
  };

  const handleSelectLocation = (location) => {
    setSelectedLocation(location);
    setAppState('dashboard');
    updateViewQuery('dashboard');
  };

  const handleOpenPhonePreview = (data) => {
    setSelectedLocation({
      ...DEFAULT_TOUR_LOCATION,
      ...(data || {}),
      initialTab: data?.initialTab || 'map'
    });
    setAppState('phone');
    updateViewQuery('phone');
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>

      {/* Main Views */}
      {appState === 'home' && (
        <HomeScreen
          onSelectFeature={(feature, data) => {
            if (feature === 'phone') {
              handleOpenPhonePreview(data);
              return;
            }

            if (feature === 'dashboard' || feature === 'chat' || feature === 'map') {
              handleSelectLocation({
                ...DEFAULT_TOUR_LOCATION,
                ...(data || {}),
                initialTab: feature === 'chat' ? 'ask' : 'map'
              });
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

      {appState === 'phone' && (
        <PhonePreview
          onBack={resetToHome}
          language={language}
          setLanguage={setLanguage}
          initialLocation={selectedLocation || { ...DEFAULT_TOUR_LOCATION, initialTab: 'map' }}
        />
      )}

    </div>
  );
}

export default App;
