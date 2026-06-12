import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  Compass,
  Landmark,
  Map as MapIcon,
  MessageSquare,
  Navigation,
  Volume2,
  WifiOff,
  X,
  Gamepad2,
  Loader2
} from 'lucide-react';
import MapExplore from '../map/MapExplore';
import UnifiedChatPage from '../voice/UnifiedChatPage';
import LanguageToggle from '../shared/LanguageToggle';
import GameHost from '../game/GameHost';
import { getNextSuggestionAPI, createGameRoomAPI } from '../../services/apiService';

const DEFAULT_LOCATION = {
  id: 1,
  name_vi: 'Kinh thành Huế (Đại Nội)',
  name_en: 'Hue Imperial City'
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
    raw: artifact
  };
};

const ArtifactDetailPanel = ({
  artifact,
  language,
  onAsk,
  onShowMap,
  assistantSteps = [],
  routeStatus = null
}) => {
  const isVi = language === 'vi';

  if (!artifact) {
    return (
      <div className="artifact-mobile-screen">
        <div className="artifact-hero-mark" aria-hidden="true">
          <Landmark size={34} />
        </div>
        <span className="screen-eyebrow">
          {isVi ? 'Điểm đang xem' : 'Current place'}
        </span>
        <h2>{isVi ? 'Chọn một điểm để bắt đầu.' : 'Choose a stop to begin.'}</h2>
        <p>
          {isVi
            ? 'Chạm vào một marker trên bản đồ Đại Nội hoặc gửi ảnh liên quan để xem thông tin phù hợp tại đây.'
            : 'Tap a marker on the Citadel map or send a related photo to see guide notes here.'}
        </p>
        <button className="tour-primary-action" onClick={onShowMap}>
          <MapIcon size={18} />
          {isVi ? 'Mở bản đồ' : 'Open map'}
        </button>
      </div>
    );
  }

  return (
    <div className="artifact-mobile-screen">
      <div className="artifact-detail-top">
        <div className="artifact-hero-mark" aria-hidden="true">
          <Landmark size={34} />
        </div>
        <div>
          <span className="screen-eyebrow">
            {isVi ? 'Điểm tham quan' : 'Tour stop'}
          </span>
          <h2>{artifact.name}</h2>
        </div>
      </div>

      <div className="artifact-fact-grid">
        <div>
          <span>{isVi ? 'Năm' : 'Year'}</span>
          <strong>{artifact.year || (isVi ? 'Đang cập nhật' : 'To be updated')}</strong>
        </div>
        <div>
          <span>{isVi ? 'Triều đại / tác giả' : 'Dynasty / author'}</span>
          <strong>{artifact.author || (isVi ? 'Chưa có dữ liệu' : 'No data yet')}</strong>
        </div>
        <div>
          <span>ID</span>
          <strong>{artifact.id || '-'}</strong>
        </div>
        {artifact.confidence !== null && (
          <div>
            <span>{isVi ? 'Độ tin cậy' : 'Confidence'}</span>
            <strong>{Math.round(Number(artifact.confidence) * 100)}%</strong>
          </div>
        )}
      </div>

      <section className="artifact-summary-block">
        <span>{isVi ? 'Tóm tắt' : 'Summary'}</span>
        <p>
          {artifact.summary || (isVi
            ? 'Thông tin chi tiết sẽ xuất hiện sau khi bạn yêu cầu AI giới thiệu hoặc đặt câu hỏi về điểm dừng này.'
            : 'Details will appear after you ask the AI guide to introduce this stop or ask a related question.')}
        </p>
      </section>

      {artifact.source && (
        <section className="artifact-summary-block">
          <span>{isVi ? 'Nguồn trả lời' : 'Answer source'}</span>
          <p>{artifact.source}</p>
        </section>
      )}

      {assistantSteps.length > 0 && (
        <section className="artifact-summary-block">
          <span>{isVi ? 'Trạng thái AI' : 'AI status'}</span>
          <ol className="artifact-step-list">
            {assistantSteps.map((step, index) => (
              <li key={`${step}-${index}`}>{step}</li>
            ))}
          </ol>
        </section>
      )}

      {routeStatus?.isNavigating && (
        <section className="artifact-summary-block">
          <span>{isVi ? 'Điều hướng' : 'Navigation'}</span>
          <p>
            {isVi ? 'Đang đi tới' : 'Walking to'} {routeStatus.targetName || artifact.name}
            {routeStatus.totalSteps > 0
              ? ` · ${isVi ? 'Bước' : 'Step'} ${routeStatus.activeStep + 1}/${routeStatus.totalSteps}`
              : ''}
          </p>
        </section>
      )}

      <div className="artifact-action-row">
        <button className="tour-primary-action" onClick={() => onAsk(artifact.raw)}>
          <Volume2 size={18} />
          {isVi ? 'Nghe giới thiệu' : 'Hear intro'}
        </button>
        <button className="tour-secondary-action" onClick={onShowMap}>
          <Navigation size={18} />
          {isVi ? 'Xem trên bản đồ' : 'View on map'}
        </button>
      </div>
    </div>
  );
};

const ExploreDashboard = ({ onBack, language, setLanguage, initialLocation }) => {
  const isVi = language === 'vi';
  const location = initialLocation || DEFAULT_LOCATION;
  const initialArtifact = location.initialArtifact || null;
  const [activeTab, setActiveTab] = useState(location.initialTab || 'map');
  const [targetArtifact, setTargetArtifact] = useState(() => (
    location.initialTab === 'ask' ? initialArtifact : null
  ));
  const [currentArtifact, setCurrentArtifact] = useState(() => initialArtifact);
  const [systemPrompt, setSystemPrompt] = useState(null);
  const [routeStatus, setRouteStatus] = useState(null);
  const [assistantSteps, setAssistantSteps] = useState([]);
  const [isOnline, setIsOnline] = useState(() => (
    typeof navigator === 'undefined' ? true : navigator.onLine
  ));
  
  // Next stop recommendation and navigation states
  const [nextSuggestion, setNextSuggestion] = useState(null);
  const [visitedIds, setVisitedIds] = useState([]);
  const [externalNavigationTarget, setExternalNavigationTarget] = useState(null);
  
  // Game states
  const [activeRoomCode, setActiveRoomCode] = useState(null);
  const [loadingGame, setLoadingGame] = useState(false);
  const [gameMinimized, setGameMinimized] = useState(false);

  useEffect(() => {
    if (!location.initialArtifact) return;
    setCurrentArtifact(location.initialArtifact);
    setTargetArtifact(location.initialTab === 'ask' ? location.initialArtifact : null);
    setActiveTab(location.initialTab || 'artifact');
  }, [location.initialArtifact, location.initialTab]);

  const handleCreateGame = async () => {
    if (visitedIds.length < 2) return;
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

  const handleNarrationFinished = useCallback(async (artifact) => {
    if (!artifact || !artifact.id) return;
    
    // Add current artifact to visited list
    setVisitedIds(prev => {
      if (prev.includes(artifact.id)) return prev;
      return [...prev, artifact.id];
    });

    try {
      const currentVisited = visitedIds.includes(artifact.id) ? visitedIds : [...visitedIds, artifact.id];
      const res = await getNextSuggestionAPI({
        currentArtifactId: artifact.id,
        visitedIds: currentVisited,
        lang: language
      });
      
      if (res.success && res.suggestions && res.suggestions.length > 0) {
        setNextSuggestion(res.suggestions[0]);
      } else {
        setNextSuggestion(null);
      }
    } catch (err) {
      console.error("Failed to load next suggestion:", err);
      setNextSuggestion(null);
    }
  }, [visitedIds, language]);

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

  const tabs = [
    { key: 'map', label: isVi ? 'Bản đồ' : 'Map', icon: MapIcon },
    { key: 'ask', label: isVi ? 'Hỏi AI' : 'Ask', icon: MessageSquare },
    { key: 'artifact', label: isVi ? 'Điểm dừng' : 'Stop', icon: Landmark }
  ];

  const handleArtifactFocus = useCallback((artifact) => {
    setCurrentArtifact(artifact);
  }, []);

  const handleNavigateToStorytelling = (artifact) => {
    if (!artifact) return;
    const normalized = normalizeArtifact(artifact, language);
    const nextArtifact = {
      ...artifact,
      id: normalized?.id || artifact?.id,
      name_vi: normalized?.nameVi || normalized?.name,
      name_en: normalized?.nameEn || normalized?.name,
      selectedAt: Date.now()
    };
    setCurrentArtifact(nextArtifact);
    setTargetArtifact(nextArtifact);
    setActiveTab('ask');
  };

  const handleAskArtifact = (artifact) => {
    if (!artifact) return;
    const normalized = normalizeArtifact(artifact, language);
    const nextArtifact = {
      ...artifact,
      id: normalized?.id || artifact?.id,
      name_vi: normalized?.nameVi || normalized?.name,
      name_en: normalized?.nameEn || normalized?.name,
      selectedAt: Date.now()
    };
    setCurrentArtifact(nextArtifact);
    setTargetArtifact(nextArtifact);
    setActiveTab('ask');
  };

  const handleMapInstruction = (text) => {
    setSystemPrompt(text);
  };

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
        <button className="tour-shell-back" onClick={onBack} aria-label={isVi ? 'Về trang chủ' : 'Back home'}>
          <ArrowLeft size={20} />
        </button>

        <div className="tour-shell-title">
          <span>{isVi ? 'Đang tham quan' : 'Now touring'}</span>
          <h1>{locationName}</h1>
        </div>

        <div className="tour-shell-actions">
          <button
            className="tour-quiz-button"
            onClick={handleCreateGame}
            disabled={visitedIds.length < 2 || loadingGame}
            title={visitedIds.length < 2 
              ? (isVi ? 'Hãy tham quan ít nhất 2 điểm để đấu trí!' : 'Visit at least 2 places to play!') 
              : (isVi ? 'Đấu trí nhóm' : 'Group quiz')}
          >
            {loadingGame ? <Loader2 className="spin" size={12} /> : <Gamepad2 size={12} />}
            <span className="tour-quiz-label">{isVi ? 'Đấu Trí Nhóm' : 'Group Quiz'}</span>
          </button>
          
          <LanguageToggle language={language} setLanguage={setLanguage} />
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

      <main className="tour-shell-stage" aria-label={isVi ? 'Không gian tham quan' : 'Tour workspace'}>
        <section className={`tour-shell-panel map-panel ${activeTab === 'map' ? 'is-active' : ''}`}>
          <MapExplore
            onNavigateToStorytelling={handleNavigateToStorytelling}
            onInstructionUpdate={handleMapInstruction}
            onArtifactFocus={handleArtifactFocus}
            onRouteStatusChange={setRouteStatus}
            language={language}
            embedded
            visitorMode
            active={activeTab === 'map'}
            externalNavigationTarget={externalNavigationTarget}
            onExternalNavigationConsumed={() => setExternalNavigationTarget(null)}
          />
        </section>

        <section className={`tour-shell-panel ask-panel ${activeTab === 'ask' ? 'is-active' : ''}`}>
          <UnifiedChatPage
            onBack={onBack}
            language={language}
            setLanguage={setLanguage}
            initialArtifact={targetArtifact}
            externalPrompt={systemPrompt}
            onArtifactUpdate={handleArtifactFocus}
            onProcessingStepsUpdate={setAssistantSteps}
            embedded
            onNarrationFinished={handleNarrationFinished}
          />
        </section>

        <section className={`tour-shell-panel artifact-panel-mobile ${activeTab === 'artifact' ? 'is-active' : ''}`}>
          <ArtifactDetailPanel
            artifact={normalizedArtifact}
            language={language}
            onAsk={handleAskArtifact}
            onShowMap={() => setActiveTab('map')}
            assistantSteps={assistantSteps}
            routeStatus={routeStatus}
          />
        </section>
      </main>

      {/* Floating recommendation card after narration completes */}
      {nextSuggestion && (
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
              onClick={() => {
                const target = nextSuggestion;
                setNextSuggestion(null);
                setExternalNavigationTarget(target);
                setActiveTab('map');
              }}
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
              {isVi ? 'Khám phá' : 'Explore'}
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

      <nav className="tour-bottom-nav" aria-label={isVi ? 'Điều hướng tham quan' : 'Tour navigation'}>
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            className={activeTab === key ? 'active' : ''}
            onClick={() => setActiveTab(key)}
            aria-current={activeTab === key ? 'page' : undefined}
          >
            <Icon size={21} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

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
          <GameHost 
            roomCode={activeRoomCode} 
            language={language} 
            onBack={() => {
              setActiveRoomCode(null);
              setGameMinimized(false);
            }} 
            onMinimize={() => setGameMinimized(true)}
          />
        </div>
      )}
    </div>
  );
};

export default ExploreDashboard;
