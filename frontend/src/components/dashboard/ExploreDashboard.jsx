import React, { Suspense, lazy, useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  BookOpen,
  Compass,
  Flag,
  Map as MapIcon,
  MessageSquare,
  Navigation,
  Volume2,
  WifiOff,
  X,
  Gamepad2,
  Loader2,
  MoreVertical,
  Play,
  Pause,
  Moon,
  Sun
} from 'lucide-react';
import MapExplore, { HUE_ARTIFACTS } from '../map/MapExplore';
import TourBottomNav from './TourBottomNav';
import TripCompletionScreen from '../passport/TripCompletionScreen';
import PhotoBoothModal from '../photoBooth/PhotoBoothModal';
import { getAllPhotoBoothFrames, getPhotoBoothFrame, PHOTO_BOOTH_COVER_FRAME } from '../../data/photoBoothFrames';
import { preloadPhotoBoothFrames } from '../../utils/photoBoothCanvas';
import { releasePhotoBoothCameraStream } from '../../utils/photoBoothCamera';
import { getNextSuggestionAPI, createGameRoomAPI, getMapConfigAPI } from '../../services/apiService';
import {
  buildTourSummary,
  clearTourMemory,
  completeTourMemory,
  loadTourMemory,
  normalizeArtifactForPassport,
  recordAudio,
  recordCheckIn,
  recordPhoto,
  recordQuestion,
  resetTourMemory
} from '../../services/tourMemoryService';

const lazyWithPreload = (factory) => {
  let modulePromise;
  const load = () => {
    modulePromise ||= factory();
    return modulePromise;
  };
  const Component = lazy(load);
  Component.preload = load;
  return Component;
};

const UnifiedChatPage = lazyWithPreload(() => import('../voice/UnifiedChatPage'));
const GameHost = lazyWithPreload(() => import('../game/GameHost'));
const TripJournal = lazyWithPreload(() => import('../passport/TripJournal'));

const DEFAULT_LOCATION = {
  id: 1,
  name_vi: 'Kinh thành Huế (Đại Nội)',
  name_en: 'Hue Imperial City'
};

const DASHBOARD_TABS = new Set(['map', 'ask', 'passport']);

const normalizeDashboardTab = (tab, fallback = 'map') => (
  DASHBOARD_TABS.has(tab) ? tab : fallback
);

const PanelLoader = ({ language }) => {
  const isVi = language === 'vi';
  return (
    <div className="tour-panel-loader" role="status" aria-live="polite">
      <span aria-hidden="true" />
      <strong>{isVi ? 'Đang mở hướng dẫn...' : 'Opening guide...'}</strong>
    </div>
  );
};

const normalizeArtifact = (artifact, language) => {
  if (!artifact) return null;
  const name = artifact.name
    || (language === 'vi' ? artifact.name_vi : artifact.name_en)
    || artifact.artifact_name
    || artifact.name_vi
    || artifact.name_en
    || '';

  return {
    id: artifact.id || artifact.artifact_id || artifact.artifactId || null,
    name,
    nameVi: artifact.name_vi || artifact.nameVi || artifact.name || '',
    nameEn: artifact.name_en || artifact.nameEn || artifact.name || '',
    year: artifact.year || artifact.artifactYear || null,
    author: artifact.author || artifact.artifactAuthor || null,
    summary: artifact.summary || artifact.artifactSummary || '',
    source: artifact.source || artifact.answerSource || '',
    confidence: artifact.confidence_score || artifact.confidenceScore || null,
    lat: artifact.lat,
    lng: artifact.lng,
    openHoursVi: artifact.openHoursVi || '',
    openHoursEn: artifact.openHoursEn || '',
    ticketVi: artifact.ticketVi || '',
    ticketEn: artifact.ticketEn || '',
    highlightVi: artifact.highlightVi || '',
    highlightEn: artifact.highlightEn || '',
    images: artifact.images || [],
    raw: artifact
  };
};

const buildTourArtifact = (artifact, language, entryAction = 'context') => {
  const normalized = normalizeArtifact(artifact, language);
  if (!artifact || !normalized) return null;
  return {
    ...artifact,
    id: normalized.id || artifact?.id,
    name_vi: normalized.nameVi || normalized.name,
    name_en: normalized.nameEn || normalized.name,
    year: normalized.year,
    author: normalized.author,
    summary: normalized.summary,
    lat: normalized.lat,
    lng: normalized.lng,
    openHoursVi: normalized.openHoursVi,
    openHoursEn: normalized.openHoursEn,
    ticketVi: normalized.ticketVi,
    ticketEn: normalized.ticketEn,
    highlightVi: normalized.highlightVi,
    highlightEn: normalized.highlightEn,
    images: normalized.images,
    entryAction,
    selectedAt: Date.now()
  };
};

const ExploreDashboard = ({ onBack, language, setLanguage, initialLocation }) => {
  const isVi = language === 'vi';
  const location = initialLocation || DEFAULT_LOCATION;
  const initialArtifact = location.initialArtifact || null;
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [globalAudio, setGlobalAudio] = useState(null);
  const [activeTab, setActiveTab] = useState(() => {
    const requestedTab = new URLSearchParams(window.location.search).get('tab');
    return normalizeDashboardTab(location.initialTab || requestedTab, 'map');
  });
  const [targetArtifact, setTargetArtifact] = useState(() => (
    location.initialTab === 'ask' ? initialArtifact : null
  ));
  const [currentArtifact, setCurrentArtifact] = useState(() => initialArtifact);
  const [routeStatus, setRouteStatus] = useState(null);
  const [isOnline, setIsOnline] = useState(() => (
    typeof navigator === 'undefined' ? true : navigator.onLine
  ));
  
  // Next stop recommendation and navigation states
  const [nextSuggestion, setNextSuggestion] = useState(null);
  const [externalNavigationTarget, setExternalNavigationTarget] = useState(null);
  
  // Game states
  const [activeRoomCode, setActiveRoomCode] = useState(null);
  const [activeHostNickname, setActiveHostNickname] = useState('');
  const [showGameNameDialog, setShowGameNameDialog] = useState(false);
  const [gameHostNameInput, setGameHostNameInput] = useState('');
  const [loadingGame, setLoadingGame] = useState(false);
  const [gameMinimized, setGameMinimized] = useState(false);
  const [hasInteractedMap, setHasInteractedMap] = useState(false);
  const [isPassportModalOpen, setIsPassportModalOpen] = useState(false);
  const [passportCatalog, setPassportCatalog] = useState(HUE_ARTIFACTS);
  const [passportMemory, setPassportMemory] = useState(() => loadTourMemory());
  const [passportToast, setPassportToast] = useState(null);
  
  // Theme state
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('tour-theme') || 'dark';
  });

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('tour-theme', theme);
  }, [theme]);
  const [showTripCompletion, setShowTripCompletion] = useState(() => (
    new URLSearchParams(window.location.search).get('trip') === 'complete'
  ));
  const [activePhotoBooth, setActivePhotoBooth] = useState(null);

  const visitedIds = useMemo(() => {
    return Object.keys(passportMemory.checkIns || {})
      .map(Number)
      .filter(Number.isFinite);
  }, [passportMemory.checkIns]);

  useEffect(() => {
    if (!location.initialArtifact) return;
    const nextTab = normalizeDashboardTab(location.initialTab, 'map');
    setCurrentArtifact(location.initialArtifact);
    setTargetArtifact(nextTab === 'ask' ? location.initialArtifact : null);
    setActiveTab(nextTab);
  }, [location.initialArtifact, location.initialTab]);

  useEffect(() => {
    let mounted = true;
    getMapConfigAPI()
      .then((data) => {
        if (mounted && data.success && data.artifacts?.length) {
          setPassportCatalog(data.artifacts);
        }
      })
      .catch((error) => {
        console.error('Failed to load passport catalog:', error);
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const storedIds = Object.keys(passportMemory.checkIns || {})
      .map((id) => Number(id))
      .filter(Number.isFinite);
    if (storedIds.length === 0) return;
    // visitedIds is derived dynamically.
  }, [passportMemory.checkIns]);

  const showPassportToast = useCallback((message) => {
    setPassportToast(message);
    window.clearTimeout(showPassportToast.timeoutId);
    showPassportToast.timeoutId = window.setTimeout(() => {
      setPassportToast(null);
    }, 3400);
  }, []);

  const handlePassportCheckIn = useCallback((artifact, details = {}) => {
    const normalized = normalizeArtifactForPassport(artifact);
    if (!normalized?.id) return;

    const wasChecked = Boolean(passportMemory.checkIns?.[String(normalized.id)]);
    setPassportMemory(prev => recordCheckIn(prev, normalized, details));

    if (!wasChecked) {
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        navigator.vibrate([50, 50, 50]); // Success vibration pattern
      }
      const name = isVi
        ? normalized.name_vi || normalized.name_en
        : normalized.name_en || normalized.name_vi;
      showPassportToast(isVi
        ? `Đã đóng dấu ${name} vào hộ chiếu.`
        : `${name} was stamped in your passport.`);
    }
  }, [isVi, passportMemory.checkIns, showPassportToast]);

  const handlePassportPhoto = useCallback((payload = {}) => {
    setPassportMemory(prev => recordPhoto(prev, payload));
  }, []);

  const handlePassportQuestion = useCallback((payload = {}) => {
    setPassportMemory(prev => recordQuestion(prev, payload));
  }, []);

  const handlePassportAudio = useCallback((payload = {}) => {
    setPassportMemory(prev => recordAudio(prev, payload));
  }, []);

  const handleResetPassport = useCallback(() => {
    const next = resetTourMemory();
    setPassportMemory(next);
    setShowTripCompletion(false);
    showPassportToast(isVi ? 'Đã làm mới hộ chiếu tham quan.' : 'Passport reset.');
  }, [isVi, showPassportToast]);

  const handleEndTrip = useCallback(() => {
    if (!passportMemory.coverPhoto) {
      setActivePhotoBooth({
        mode: 'cover',
        frame: PHOTO_BOOTH_COVER_FRAME,
        artifact: null
      });
      return;
    }
    setPassportMemory(prev => completeTourMemory(prev));
    setShowTripCompletion(true);
  }, [passportMemory.coverPhoto]);

  const handleOpenPhotoBooth = useCallback((artifact) => {
    const normalized = normalizeArtifactForPassport(artifact);
    const frame = getPhotoBoothFrame(normalized?.id);
    if (!frame || !normalized) return;
    setActivePhotoBooth({
      mode: 'checkin',
      frame,
      artifact: normalized
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    preloadPhotoBoothFrames(getAllPhotoBoothFrames())
      .then((result) => {
        if (!cancelled && result.failed.length > 0) {
          console.warn('Some photo booth frames failed to preload:', result.failed);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          console.warn('Photo booth frame preload failed:', error);
        }
      });

    return () => {
      cancelled = true;
      releasePhotoBoothCameraStream();
    };
  }, []);

  const handleSavePhotoBooth = useCallback(({ imageBase64, frame, artifact, mode }) => {
    const isCover = mode === 'cover';
    const payload = {
      artifact,
      imageBase64,
      type: isCover ? 'cover' : 'checkin',
      source: 'photo_booth',
      frameKey: frame?.key || ''
    };

    setPassportMemory(prev => {
      const withPhoto = recordPhoto(prev, payload);
      return isCover ? completeTourMemory(withPhoto) : recordCheckIn(withPhoto, artifact, { method: 'photo_booth', source: 'photo_booth' });
    });

    setActivePhotoBooth(null);
    if (isCover) {
      setShowTripCompletion(true);
      showPassportToast(isVi ? 'Đã lưu ảnh bìa chuyến đi.' : 'Trip cover saved.');
      return;
    }

    const name = isVi
      ? artifact?.name_vi || artifact?.name_en
      : artifact?.name_en || artifact?.name_vi;
    showPassportToast(isVi ? `Đã lưu ảnh check-in ${name}.` : `${name} check-in photo saved.`);
  }, [isVi, showPassportToast]);

  const handleTripCompletionHome = useCallback(() => {
    releasePhotoBoothCameraStream();
    const next = clearTourMemory();
    setPassportMemory(next);
    setShowTripCompletion(false);
    setNextSuggestion(null);
    onBack?.();
  }, [onBack]);

  const handleBackFromTour = useCallback(() => {
    releasePhotoBoothCameraStream();
    onBack?.();
  }, [onBack]);

  const handleCreateGame = async () => {
    if (visitedIds.length < 2) return;
    GameHost.preload();
    setGameHostNameInput(activeHostNickname || '');
    setShowGameNameDialog(true);
  };

  const handleConfirmCreateGame = async (event) => {
    event?.preventDefault();
    if (visitedIds.length < 2) return;
    const hostNickname = gameHostNameInput.trim();
    if (!hostNickname) return;
    try {
      setLoadingGame(true);
      const res = await createGameRoomAPI(visitedIds, language, hostNickname);
      if (res.success && res.room_code) {
        setActiveHostNickname(hostNickname);
        setActiveRoomCode(res.room_code);
        setShowGameNameDialog(false);
        setGameMinimized(false);
      }
    } catch (err) {
      console.error("Failed to create quiz room:", err);
      alert(isVi 
        ? "Có lỗi xảy ra khi tạo phòng đấu trí nhóm. Vui lòng thử lại!" 
        : "Failed to create group quiz room. Please try again!");
    } finally {
      setLoadingGame(false);
    }
  };

  const loadNextSuggestionForArtifact = useCallback(async (artifact) => {
    const normalized = normalizeArtifact(artifact || currentArtifact, language);
    if (!normalized?.id) return null;

    handlePassportCheckIn(normalized, { method: 'manual', source: 'next_suggestion' });

    const currentVisited = visitedIds.includes(normalized.id)
      ? visitedIds
      : [...visitedIds, normalized.id];

    try {
      const res = await getNextSuggestionAPI({
        currentArtifactId: normalized.id,
        visitedIds: currentVisited,
        lang: language
      });

      const suggestion = res.success && res.suggestions?.length > 0
        ? res.suggestions[0]
        : null;
      setNextSuggestion(suggestion);
      return suggestion;
    } catch (err) {
      console.error("Failed to load next suggestion:", err);
      setNextSuggestion(null);
      return null;
    }
  }, [currentArtifact, language, visitedIds, handlePassportCheckIn]);

  const handleNarrationFinished = useCallback(async (artifact) => {
    await loadNextSuggestionForArtifact(artifact);
  }, [loadNextSuggestionForArtifact]);

  useEffect(() => {
    const updateOnline = () => setIsOnline(true);
    const updateOffline = () => setIsOnline(false);
    window.addEventListener('online', updateOnline);
    window.addEventListener('offline', updateOffline);
    return () => {
      window.removeEventListener('online', updateOnline);
      window.removeEventListener('offline', updateOffline);
    };
  }, []);

  const normalizedArtifact = useMemo(
    () => normalizeArtifact(currentArtifact, language),
    [currentArtifact, language]
  );

  const passportSummary = useMemo(
    () => buildTourSummary(passportMemory, passportCatalog, language),
    [passportMemory, passportCatalog, language]
  );

  const tabs = [
    { key: 'map', label: isVi ? 'Bản đồ' : 'Map', icon: MapIcon },
    { key: 'ask', label: isVi ? 'Hỏi AI' : 'Ask AI', icon: MessageSquare },
    {
      key: 'game',
      label: loadingGame ? (isVi ? 'Đang tạo' : 'Creating') : (isVi ? 'Chơi game' : 'Game'),
      icon: Gamepad2,
      onSelect: handleCreateGame,
      disabled: loadingGame || visitedIds.length < 2,
      title: visitedIds.length < 2
        ? (isVi ? 'Check-in ít nhất 2 địa điểm để chơi game' : 'Check in at least 2 stops to play')
        : (isVi ? 'Mở chế độ chơi game' : 'Open game mode')
    }
  ];

  const handleArtifactFocus = useCallback((artifact) => {
    const nextArtifact = buildTourArtifact(artifact, language, 'context') || artifact;
    setCurrentArtifact(nextArtifact);
  }, [language]);

  const handleMapArtifactFocus = useCallback((artifact) => {
    setHasInteractedMap(true);
    handleArtifactFocus(artifact);
    setNextSuggestion(null);
  }, [handleArtifactFocus]);

  const openArtifactInGuide = useCallback((artifact, entryAction = 'intro') => {
    if (!artifact) return;
    UnifiedChatPage.preload();
    const nextArtifact = buildTourArtifact(artifact, language, entryAction);
    if (!nextArtifact) return;
    setCurrentArtifact(nextArtifact);
    setTargetArtifact(nextArtifact);
    setActiveTab('ask');
  }, [language]);

  const handleNavigateToStorytelling = (artifact) => {
    openArtifactInGuide(artifact, 'intro');
  };



  const handleOpenArtifactContext = (artifact) => {
    openArtifactInGuide(artifact, 'context');
  };

  const handleUseNextSuggestion = useCallback((suggestion, mode = 'route') => {
    if (!suggestion) return;
    const nextArtifact = buildTourArtifact(suggestion, language, mode === 'intro' ? 'intro' : 'context');
    if (!nextArtifact) return;
    setNextSuggestion(null);
    setCurrentArtifact(nextArtifact);
    if (mode === 'intro') {
      UnifiedChatPage.preload();
      setTargetArtifact(nextArtifact);
      setActiveTab('ask');
      return;
    }
    setExternalNavigationTarget(nextArtifact);
    setActiveTab('map');
  }, [language]);

  const locationName = isVi
    ? (location.name_vi || DEFAULT_LOCATION.name_vi)
    : (location.name_en || location.name_vi || DEFAULT_LOCATION.name_en);

  const activeRouteTarget = routeStatus?.targetName;
  const routeStepLabel = routeStatus?.isNavigating && routeStatus.totalSteps > 0
    ? `${routeStatus.activeStep + 1}/${routeStatus.totalSteps}`
    : '';



  return (
    <div className="mobile-tour-shell">
      <header className="tour-shell-header">
        <button className="tour-shell-back" onClick={handleBackFromTour} aria-label={isVi ? 'Về trang chủ' : 'Back home'}>
          <ArrowLeft size={20} />
        </button>

        <div className="tour-shell-title">
          <span>{isVi ? 'Đang tham quan' : 'Now touring'}</span>
          <h1>{locationName}</h1>
        </div>

        <div className="tour-shell-actions-simplified">
          
          <button 
            onClick={() => setIsPassportModalOpen(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '6px 12px', borderRadius: 'var(--radius-full)',
              background: 'var(--color-bg-surface-glass)', border: '1px solid var(--color-border)',
              color: 'var(--color-primary)', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)'
            }}
            title={isVi ? 'Hộ chiếu' : 'Passport'}
          >
            <BookOpen size={16} />
            <span>{passportSummary.completedCount}/{passportSummary.totalCount}</span>
          </button>

          <button
            onClick={handleCreateGame}
            disabled={loadingGame || visitedIds.length < 2}
            className="tour-header-game-button"
            title={visitedIds.length < 2
              ? (isVi ? 'Check-in ít nhất 2 địa điểm để chơi game' : 'Check in at least 2 stops to play')
              : (isVi ? 'Chơi game' : 'Play game')}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px',
              minWidth: '34px', height: '34px', borderRadius: 'var(--radius-full)',
              padding: '0 10px',
              background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
              color: '#101818', border: '1px solid rgba(212, 175, 55, 0.35)',
              boxShadow: 'var(--shadow-sm)',
              cursor: loadingGame || visitedIds.length < 2 ? 'not-allowed' : 'pointer',
              opacity: loadingGame || visitedIds.length < 2 ? 0.58 : 1,
              fontSize: '12px', fontWeight: '900'
            }}
          >
            <Gamepad2 size={16} />
            <span className="tour-header-game-label">{loadingGame ? (isVi ? 'Tạo' : 'New') : (isVi ? 'Game' : 'Game')}</span>
          </button>

          <button 
            onClick={handleEndTrip}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: '34px', height: '34px', borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--color-accent), var(--color-accent-dark))',
              color: 'white', border: 'none', boxShadow: 'var(--shadow-md)', cursor: 'pointer'
            }}
            title={isVi ? 'Kết thúc hành trình' : 'End Trip'}
          >
            <Flag size={16} />
          </button>

          <button 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="header-icon-btn"
            aria-label="Toggle Theme"
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: '34px', height: '34px', borderRadius: '50%',
              background: 'transparent', color: 'var(--color-text-main)', 
              border: '1px solid var(--color-border)', cursor: 'pointer',
              marginLeft: '4px'
            }}
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <button 
            onClick={() => setLanguage(language === 'vi' ? 'en' : 'vi')}
            className="header-icon-btn"
            aria-label="Toggle Language"
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: '34px', height: '34px', borderRadius: '50%',
              background: 'transparent', color: 'var(--color-text-main)', 
              border: '1px solid var(--color-border)', cursor: 'pointer',
              marginLeft: '4px', fontSize: '12px', fontWeight: 'bold'
            }}
          >
            {language === 'vi' ? 'EN' : 'VI'}
          </button>
        </div>
      </header>

      {!isOnline && (
        <div className="tour-offline-banner" role="status">
          <WifiOff size={16} />
          <span>
            {isVi
              ? 'Đang mất kết nối. Bạn vẫn có thể xem phần đã tải và thử lại khi có mạng.'
              : 'You are offline. Loaded content remains available; retry when the connection returns.'}
          </span>
        </div>
      )}

      {passportToast && (
        <div className="passport-toast" role="status" aria-live="polite">
          <BookOpen size={16} />
          <span>{passportToast}</span>
        </div>
      )}

      <main className="tour-shell-stage" aria-label={isVi ? 'Không gian tham quan' : 'Tour workspace'}>
        <section className={`tour-shell-panel map-panel ${activeTab === 'map' ? 'is-active' : ''}`}>
          <MapExplore
            onNavigateToStorytelling={handleNavigateToStorytelling}
            onOpenArtifactContext={handleOpenArtifactContext}
            onArtifactFocus={handleMapArtifactFocus}
            onRouteStatusChange={setRouteStatus}
            onPassportCheckIn={handlePassportCheckIn}
            onPhotoBooth={handleOpenPhotoBooth}
            language={language}
            embedded
            visitorMode
            active={activeTab === 'map'}
            externalNavigationTarget={externalNavigationTarget}
            onExternalNavigationConsumed={() => setExternalNavigationTarget(null)}
            focusedArtifactId={normalizedArtifact?.id || null}
          />
        </section>

        <section className={`tour-shell-panel ask-panel ${activeTab === 'ask' ? 'is-active' : ''}`}>
          <Suspense fallback={<PanelLoader language={language} />}>
            <UnifiedChatPage
              embedded={true}
              onBack={() => setActiveTab('map')}
              language={language}
              setLanguage={setLanguage}
              initialArtifact={targetArtifact}
              onArtifactUpdate={handleArtifactFocus}
              onNarrationFinished={handleNarrationFinished}
              onRequestNextStop={loadNextSuggestionForArtifact}
              onPassportCheckIn={handlePassportCheckIn}
              onPassportPhoto={handlePassportPhoto}
              onPassportQuestion={handlePassportQuestion}
              onPassportAudio={handlePassportAudio}
              onShowMap={() => setActiveTab('map')}
              onGlobalAudioUpdate={setGlobalAudio}
            />
          </Suspense>
        </section>

      </main>

      {/* Passport Overlay Modal */}
      {isPassportModalOpen && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)',
          zIndex: 5000, display: 'flex', flexDirection: 'column',
          justifyContent: 'flex-end', animation: 'fadeIn 0.2s ease-out'
        }}>
          <div style={{
            background: 'var(--color-bg-dark)',
            borderTopLeftRadius: '24px', borderTopRightRadius: '24px',
            height: '85vh', display: 'flex', flexDirection: 'column',
            boxShadow: '0 -10px 40px rgba(0,0,0,0.5)',
            animation: 'slideUp 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
          }}>
            <div style={{ padding: '20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ margin: 0, color: 'var(--color-primary)', fontFamily: 'var(--font-heading)', fontSize: '20px' }}>
                {isVi ? 'Hộ chiếu của bạn' : 'Your Passport'}
              </h2>
              <button onClick={() => setIsPassportModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--color-text-main)', cursor: 'pointer', display: 'flex', padding: '4px' }}>
                 <X size={24} />
              </button>
            </div>
            
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px', paddingBottom: '40px' }}>
               <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
                  <div style={{ flex: 1, background: 'var(--color-bg-surface)', padding: '16px', borderRadius: '16px', border: '1px solid var(--color-border)', textAlign: 'center' }}>
                    <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{isVi ? 'Dấu mộc' : 'Stamps'}</span>
                    <strong style={{ fontSize: '24px', color: 'var(--color-primary)', display: 'block', marginTop: '4px' }}>{passportSummary.completedCount}/{passportSummary.totalCount}</strong>
                  </div>
                  <div style={{ flex: 1, background: 'var(--color-bg-surface)', padding: '16px', borderRadius: '16px', border: '1px solid var(--color-border)', textAlign: 'center' }}>
                    <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{isVi ? 'Nhật ký' : 'Journal'}</span>
                    <strong style={{ fontSize: '24px', color: 'var(--color-primary)', display: 'block', marginTop: '4px' }}>{passportSummary.photos.length + passportSummary.questions.length + passportSummary.audio.length}</strong>
                  </div>
               </div>
               
               <Suspense fallback={<PanelLoader language={language} />}>
                  <TripJournal
                    language={language}
                    catalog={passportCatalog}
                    memory={passportMemory}
                    onResetMemory={handleResetPassport}
                  />
               </Suspense>
            </div>
          </div>
        </div>
      )}

      {/* Global Mini Player for Audio */}
      {globalAudio && activeTab !== 'ask' && (
        <div style={{
          position: 'absolute',
          bottom: '80px', /* Above BottomNav */
          left: '16px',
          right: '16px',
          background: 'rgba(255, 253, 246, 0.96)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(16, 24, 24, 0.12)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 3000,
          animation: 'slideUp 0.3s ease-out'
        }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white'
          }}>
            <Volume2 size={18} />
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontSize: '10px', color: '#7a4f00', textTransform: 'uppercase', fontWeight: 'bold', whiteSpace: 'nowrap' }}>
              {isVi ? 'Đang đọc' : 'Reading'}
            </div>
            <div style={{ fontSize: '13px', color: '#101818', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {globalAudio.title}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
            <button 
              onClick={() => window.dispatchEvent(new CustomEvent('tour:audio:toggle'))}
              style={{
                width: '32px', height: '32px', borderRadius: '50%', border: 'none',
                background: 'rgba(16,24,24,0.08)', color: '#101818',
                display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
              }}
            >
              {globalAudio.state === 'playing' ? <Pause size={16} /> : <Play size={16} />}
            </button>
            <button 
              onClick={() => window.dispatchEvent(new CustomEvent('tour:audio:stop'))}
              style={{
                width: '32px', height: '32px', borderRadius: '50%', border: 'none',
                background: 'transparent', color: '#33413d',
                display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
              }}
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Pulsing Onboarding Tooltip */}
      {activeTab === 'map' && !hasInteractedMap && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
          zIndex: 2000,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px'
        }}>
          <div style={{
            background: 'var(--color-primary)',
            color: 'var(--color-bg-dark)',
            padding: '8px 16px',
            borderRadius: 'var(--radius-full)',
            fontSize: '13px',
            fontWeight: 'bold',
            boxShadow: 'var(--shadow-lg)',
            animation: 'pulse 2s infinite',
            whiteSpace: 'nowrap'
          }}>
            {isVi ? 'Chạm vào điểm đến trên bản đồ' : 'Tap on a destination'}
          </div>
          <div style={{
            width: '0',
            height: '0',
            borderLeft: '6px solid transparent',
            borderRight: '6px solid transparent',
            borderTop: '6px solid var(--color-primary)',
            animation: 'pulse 2s infinite'
          }}></div>
        </div>
      )}

      {activePhotoBooth && (
        <PhotoBoothModal
          frame={activePhotoBooth.frame}
          artifact={activePhotoBooth.artifact}
          mode={activePhotoBooth.mode}
          language={language}
          onClose={() => setActivePhotoBooth(null)}
          onSave={handleSavePhotoBooth}
        />
      )}

      {showTripCompletion && (
        <TripCompletionScreen
          language={language}
          catalog={passportCatalog}
          memory={passportMemory}
          onBackToTour={() => setShowTripCompletion(false)}
          onBackHome={handleTripCompletionHome}
          onResetMemory={handleResetPassport}
        />
      )}

      {/* Floating recommendation card after narration completes */}
      {nextSuggestion && activeTab !== 'ask' && (
        <div style={{
          position: 'absolute',
          bottom: '80px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: 'calc(100% - 32px)',
          maxWidth: '380px',
          backgroundColor: 'rgba(255, 253, 246, 0.96)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(16, 24, 24, 0.12)',
          borderRadius: 'var(--radius-lg)',
          padding: '12px 16px',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          zIndex: 2000,
          animation: 'slideUp 0.3s ease-out'
        }}>
          <div style={{ flex: 1, textAlign: 'left' }}>
            <span style={{ fontSize: '10px', color: '#7a4f00', fontWeight: '700', textTransform: 'uppercase', display: 'block', letterSpacing: '0.5px' }}>
              {isVi ? 'GỢI Ý ĐIỂM TIẾP THEO' : 'RECOMMENDED NEXT STOP'}
            </span>
            <strong style={{ fontSize: '14px', color: '#101818', display: 'block', margin: '2px 0' }}>
              {isVi ? nextSuggestion.name_vi : nextSuggestion.name_en}
            </strong>
            <span style={{ fontSize: '11px', color: '#42524f', display: 'block' }}>
              {nextSuggestion.reason} ({nextSuggestion.distance}m · {Math.ceil(nextSuggestion.walk_duration_min)} {isVi ? 'phút đi bộ' : 'min walk'})
            </span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button 
              onClick={() => handleUseNextSuggestion(nextSuggestion, 'route')}
              style={{
                background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
                color: '#101818',
                border: 'none',
                padding: '8px 14px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: 'var(--shadow-md)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Navigation size={12} />
              {isVi ? 'Đường đi' : 'Route'}
            </button>
            <button 
              onClick={() => handleUseNextSuggestion(nextSuggestion, 'intro')}
              style={{
                backgroundColor: '#fffdf6',
                color: '#0f5f59',
                border: '1px solid rgba(15, 95, 89, 0.22)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Volume2 size={12} />
              {isVi ? 'Nghe trước' : 'Preview'}
            </button>
            <button 
              onClick={() => setNextSuggestion(null)}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                color: '#999',
                cursor: 'pointer',
                padding: '4px'
              }}
              aria-label={isVi ? 'Đóng' : 'Close'}
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {routeStatus?.isNavigating && activeTab !== 'map' && (
        <button className="route-mini-bar" onClick={() => setActiveTab('map')}>
          <Compass size={18} />
          <span>
            {isVi ? 'Đang đi tới' : 'Walking to'} {activeRouteTarget || (isVi ? 'điểm đã chọn' : 'selected stop')}
          </span>
          {routeStepLabel && <strong>{routeStepLabel}</strong>}
        </button>
      )}

      <TourBottomNav
        tabs={tabs}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isVi={isVi}
        onPreloadChat={UnifiedChatPage.preload}
      />

      {showGameNameDialog && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={isVi ? 'Đặt tên người chơi' : 'Set player name'}
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 5200,
            display: 'grid',
            placeItems: 'center',
            padding: '20px',
            background: 'rgba(16, 24, 24, 0.62)',
            backdropFilter: 'blur(8px)'
          }}
        >
          <form
            onSubmit={handleConfirmCreateGame}
            style={{
              width: 'min(420px, 100%)',
              display: 'grid',
              gap: '14px',
              padding: '22px',
              borderRadius: '8px',
              background: '#fffdf6',
              border: '1px solid rgba(16,24,24,0.12)',
              boxShadow: '0 24px 70px rgba(0,0,0,0.24)'
            }}
          >
            <div style={{ display: 'grid', gap: '6px' }}>
              <span style={{ color: '#7a4f00', fontSize: '12px', fontWeight: 900, textTransform: 'uppercase' }}>
                {isVi ? 'Chủ phòng cùng tham gia' : 'Host joins as player'}
              </span>
              <h2 style={{ margin: 0, color: '#101818', fontSize: '22px', lineHeight: 1.15 }}>
                {isVi ? 'Đặt tên để vào phòng chơi' : 'Name yourself to start'}
              </h2>
              <p style={{ margin: 0, color: '#42524f', fontSize: '13px', lineHeight: 1.5 }}>
                {isVi
                  ? 'Tên này sẽ xuất hiện trong bảng điểm và được gắn nhãn Chủ phòng.'
                  : 'This name appears on the scoreboard with a Host tag.'}
              </p>
            </div>
            <input
              value={gameHostNameInput}
              maxLength={20}
              autoFocus
              onChange={(event) => setGameHostNameInput(event.target.value)}
              placeholder={isVi ? 'Tên của bạn...' : 'Your name...'}
              style={{
                width: '100%',
                minHeight: '46px',
                padding: '0 13px',
                borderRadius: '8px',
                border: '1.5px solid rgba(16,24,24,0.18)',
                color: '#101818',
                background: '#ffffff',
                fontSize: '15px',
                fontWeight: 800,
                outline: 'none'
              }}
            />
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => setShowGameNameDialog(false)}
                disabled={loadingGame}
                style={{
                  minHeight: '42px',
                  padding: '0 14px',
                  borderRadius: '8px',
                  border: '1px solid rgba(16,24,24,0.14)',
                  color: '#101818',
                  background: '#fffdf6',
                  fontWeight: 850,
                  cursor: 'pointer'
                }}
              >
                {isVi ? 'Hủy' : 'Cancel'}
              </button>
              <button
                type="submit"
                disabled={loadingGame || !gameHostNameInput.trim()}
                style={{
                  minHeight: '42px',
                  padding: '0 16px',
                  borderRadius: '8px',
                  border: 'none',
                  color: '#fffaf0',
                  background: loadingGame || !gameHostNameInput.trim() ? '#9aa4a0' : '#0f5f59',
                  fontWeight: 900,
                  cursor: loadingGame || !gameHostNameInput.trim() ? 'not-allowed' : 'pointer'
                }}
              >
                {loadingGame ? (isVi ? 'Đang tạo...' : 'Creating...') : (isVi ? 'Vào chơi' : 'Join game')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Floating banner when game is minimized */}
      {activeRoomCode && gameMinimized && (
        <div style={{
          position: 'absolute',
          top: '60px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: 'calc(100% - 32px)',
          maxWidth: '380px',
          background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
          color: '#fff',
          borderRadius: 'var(--radius-md)',
          padding: '10px 16px',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 4000,
          animation: 'slideDown 0.3s ease-out'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '18px' }}>🎮</span>
            <span style={{ fontSize: '13px', fontWeight: '700' }}>
              {isVi ? `Trò chơi đang diễn ra (${activeRoomCode})` : `Active Quiz Room (${activeRoomCode})`}
            </span>
          </div>
          <button
            onClick={() => setGameMinimized(false)}
            style={{
              backgroundColor: 'var(--color-bg-surface)',
              color: 'var(--color-text-main)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 12px',
              fontSize: '11px',
              fontWeight: '800',
              cursor: 'pointer'
            }}
          >
            {isVi ? 'Quay lại game' : 'Resume Game'}
          </button>
        </div>
      )}

      {/* Game Host Overlay keep-alive */}
      {activeRoomCode && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 5000,
          backgroundColor: '#fff',
          display: gameMinimized ? 'none' : 'flex',
          flexDirection: 'column'
        }}>
          <Suspense fallback={<PanelLoader language={language} />}>
            <GameHost
              roomCode={activeRoomCode}
              hostNickname={activeHostNickname}
              language={language}
              onBack={() => {
                setActiveRoomCode(null);
                setActiveHostNickname('');
                setGameMinimized(false);
              }}
              onMinimize={() => setGameMinimized(true)}
            />
          </Suspense>
        </div>
      )}
    </div>
  );
};

export default ExploreDashboard;
