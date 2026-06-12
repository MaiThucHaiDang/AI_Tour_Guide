import React, { useState, useEffect } from 'react';
import HomeScreen from './components/HomeScreen';
import ExploreDashboard from './components/dashboard/ExploreDashboard';
import MapCalibrate from './components/map/MapCalibrate';
import PhonePreview from './components/PhonePreview';
import GamePlayer from './components/game/GamePlayer';
import DestinationDetail from './components/destinations/DestinationDetail';
import { getDestinationById } from './data/destinations';

const DEFAULT_TOUR_LOCATION = {
  id: 1,
  name_vi: 'Kinh thành Huế (Đại Nội)',
  name_en: 'Hue Imperial City'
};

const updateViewQuery = (view, params = {}) => {
  const url = new URL(window.location.href);
  url.searchParams.delete('destination');
  if (view === 'home') {
    url.searchParams.delete('view');
  } else {
    url.searchParams.set('view', view);
  }
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  });
  window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
};

const destinationToTourArtifact = (destination, language) => ({
  id: destination.artifactId || destination.id,
  name_vi: destination.nameVi,
  name_en: destination.nameEn,
  year: destination.year,
  author: language === 'vi' ? destination.authorVi : destination.authorEn,
  summary: language === 'vi' ? destination.summaryVi : destination.summaryEn,
  lat: destination.lat,
  lng: destination.lng
});

const getInitialDestinationFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  return getDestinationById(params.get('destination'));
};

function App() {
  const isPhoneFrame = new URLSearchParams(window.location.search).get('frame') === 'phone';
  const [appState, setAppState] = useState(() => {
    const view = new URLSearchParams(window.location.search).get('view');
    if (view === 'calibrate') return 'calibrate';
    if (view === 'phone') return 'phone';
    if (view === 'join') return 'join';
    if (view === 'destination' && getInitialDestinationFromUrl()) return 'destination';
    return view === 'dashboard' ? 'dashboard' : 'home';
  });
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('ai_tour_lang') || 'vi';
  });
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState(() => {
    return getInitialDestinationFromUrl();
  });

  useEffect(() => {
    localStorage.setItem('ai_tour_lang', language);
  }, [language]);

  const resetToHome = () => {
    setAppState('home');
    setSelectedLocation(null);
    setSelectedDestination(null);
    updateViewQuery('home');
  };

  const backToDestinationList = () => {
    resetToHome();
    window.setTimeout(() => {
      document.getElementById('places')?.scrollIntoView({ block: 'start' });
    }, 0);
  };

  const handleSelectLocation = (location) => {
    setSelectedLocation(location);
    setAppState('dashboard');
    updateViewQuery('dashboard');
  };

  const handleSelectDestination = (destination) => {
    setSelectedDestination(destination);
    setAppState('destination');
    updateViewQuery('destination', { destination: destination.id });
  };

  const handleStartDestinationTour = (destination, initialTab = 'artifact') => {
    setSelectedLocation({
      id: destination.id,
      type: 'destination',
      name_vi: destination.nameVi,
      name_en: destination.nameEn,
      initialTab,
      initialArtifact: destinationToTourArtifact(destination, language),
      selectedAt: Date.now()
    });
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
    <div
      className={`app-root ${isPhoneFrame ? 'is-phone-frame' : ''}`}
      style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}
    >

      {/* Main Views */}
      {appState === 'home' && (
        <HomeScreen
          onSelectFeature={(feature, data) => {
            if (feature === 'phone') {
              if (isPhoneFrame) {
                handleSelectLocation({ ...DEFAULT_TOUR_LOCATION, ...(data || {}), initialTab: 'map' });
                return;
              }
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
          isPhoneFrame={isPhoneFrame}
          onSelectDestination={handleSelectDestination}
        />
      )}

      {appState === 'destination' && selectedDestination && (
        <DestinationDetail
          destination={selectedDestination}
          language={language}
          onBack={backToDestinationList}
          onStartTour={(destination) => handleStartDestinationTour(destination, 'artifact')}
          onAskGuide={(destination) => handleStartDestinationTour(destination, 'ask')}
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
        />
      )}

      {appState === 'join' && (
        <GamePlayer
          roomCode={new URLSearchParams(window.location.search).get('code') || ''}
          language={language}
          onBack={resetToHome}
        />
      )}

    </div>
  );
}

export default App;
