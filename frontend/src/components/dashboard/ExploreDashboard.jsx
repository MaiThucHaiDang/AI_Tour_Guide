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
  MoreVertical
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

const DEFAULT_LOCATION = {
  id: 1,
  name_vi: 'Kinh thành Huế (Đại Nội)',
  name_en: 'Hue Imperial City'
};

const DASHBOARD_TABS = new Set(['map', 'ask']);

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
  const [loadingGame, setLoadingGame] = useState(false);
  const [gameMinimized, setGameMinimized] = useState(false);
  const [passportCatalog, setPassportCatalog] = useState(HUE_ARTIFACTS);
  const [passportMemory, setPassportMemory] = useState(() => loadTourMemory());
  const [passportToast, setPassportToast] = useState(null);
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
    try {
      setLoadingGame(true);
      const res = await createGameRoomAPI(visitedIds, language);
      if (res.success && res.room_code) {
        setActiveRoomCode(res.room_code);
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
    { key: 'ask', label: isVi ? 'Hỏi hướng dẫn' : 'Ask guide', icon: MessageSquare }
  ];

  const handleArtifactFocus = useCallback((artifact) => {
    const nextArtifact = buildTourArtifact(artifact, language, 'context') || artifact;
    setCurrentArtifact(nextArtifact);
  }, [language]);

  const handleMapArtifactFocus = useCallback((artifact) => {
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
            className="tour-menu-toggle-btn" 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label={isVi ? 'Danh mục chức năng' : 'Menu actions'}
            aria-expanded={isMenuOpen}
          >
            <MoreVertical size={20} />
          </button>

          {isMenuOpen && (
            <>
              <div className="tour-menu-backdrop" onClick={() => setIsMenuOpen(false)} />
              <div className="tour-menu-dropdown">
                <div className="tour-menu-item passport-progress">
                  <BookOpen size={16} />
                  <div>
                    <span>{isVi ? 'Hộ chiếu tham quan' : 'Tour Passport'}</span>
                    <strong>{passportSummary.completedCount}/{passportSummary.totalCount}</strong>
                  </div>
                </div>

                <button 
                  className="tour-menu-item action-btn" 
                  onClick={() => {
                    handleCreateGame();
                    setIsMenuOpen(false);
                  }}
                  disabled={visitedIds.length < 2 || loadingGame}
                  title={visitedIds.length < 2 ? (isVi ? 'Tham quan ít nhất 2 điểm để chơi' : 'Visit at least 2 stops to play') : ''}
                >
                  {loadingGame ? <Loader2 className="spin" size={16} /> : <Gamepad2 size={16} />}
                  <span>{isVi ? 'Đấu Trí Nhóm' : 'Group Quiz'}</span>
                </button>

                <div className="tour-menu-item lang-toggle-row">
                  <span>{isVi ? 'Ngôn ngữ' : 'Language'}</span>
                  <div className="lang-buttons">
                    <button 
                      className={language === 'vi' ? 'active' : ''} 
                      onClick={() => {
                        setLanguage('vi');
                        setIsMenuOpen(false);
                      }}
                    >
                      VI
                    </button>
                    <button 
                      className={language === 'en' ? 'active' : ''} 
                      onClick={() => {
                        setLanguage('en');
                        setIsMenuOpen(false);
                      }}
                    >
                      EN
                    </button>
                  </div>
                </div>

                <button 
                  className="tour-menu-item action-btn end-trip" 
                  onClick={() => {
                    handleEndTrip();
                    setIsMenuOpen(false);
                  }}
                >
                  <Flag size={16} />
                  <span>{isVi ? 'Kết thúc chuyến đi' : 'End Trip'}</span>
                </button>
              </div>
            </>
          )}
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
              onBack={onBack}
              language={language}
              setLanguage={setLanguage}
              initialArtifact={targetArtifact}
              onArtifactUpdate={handleArtifactFocus}
              embedded
              onNarrationFinished={handleNarrationFinished}
              onRequestNextStop={loadNextSuggestionForArtifact}
              onPassportCheckIn={handlePassportCheckIn}
              onPassportPhoto={handlePassportPhoto}
              onPassportQuestion={handlePassportQuestion}
              onPassportAudio={handlePassportAudio}
              onShowMap={() => setActiveTab('map')}
            />
          </Suspense>
        </section>
      </main>

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
          backgroundColor: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(10px)',
          borderRadius: '16px',
          padding: '12px 16px',
          boxShadow: '0 8px 32px rgba(15, 95, 89, 0.15)',
          border: '1px solid rgba(15, 95, 89, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          zIndex: 2000,
          animation: 'slideUp 0.3s ease-out'
        }}>
          <div style={{ flex: 1, textAlign: 'left' }}>
            <span style={{ fontSize: '10px', color: '#b2820a', fontWeight: '700', textTransform: 'uppercase', display: 'block', letterSpacing: '0.5px' }}>
              {isVi ? 'GỢI Ý ĐIỂM TIẾP THEO' : 'RECOMMENDED NEXT STOP'}
            </span>
            <strong style={{ fontSize: '14px', color: '#0f5f59', display: 'block', margin: '2px 0' }}>
              {isVi ? nextSuggestion.name_vi : nextSuggestion.name_en}
            </strong>
            <span style={{ fontSize: '11px', color: '#666', display: 'block' }}>
              {nextSuggestion.reason} ({nextSuggestion.distance}m · {Math.ceil(nextSuggestion.walk_duration_min)} {isVi ? 'phút đi bộ' : 'min walk'})
            </span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button 
              onClick={() => handleUseNextSuggestion(nextSuggestion, 'route')}
              style={{
                backgroundColor: '#0f5f59',
                color: '#fff',
                border: 'none',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 3px 8px rgba(15, 95, 89, 0.3)',
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
                backgroundColor: '#fffaf0',
                color: '#0f5f59',
                border: '1px solid rgba(15, 95, 89, 0.22)',
                padding: '8px 12px',
                borderRadius: '8px',
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

      {/* Floating banner when game is minimized */}
      {activeRoomCode && gameMinimized && (
        <div style={{
          position: 'absolute',
          top: '60px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: 'calc(100% - 32px)',
          maxWidth: '380px',
          backgroundColor: '#0f5f59',
          color: '#fff',
          borderRadius: '12px',
          padding: '10px 16px',
          boxShadow: '0 4px 15px rgba(15,95,89,0.3)',
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
              backgroundColor: '#fff',
              color: '#0f5f59',
              border: 'none',
              borderRadius: '8px',
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
              language={language}
              onBack={() => {
                setActiveRoomCode(null);
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
