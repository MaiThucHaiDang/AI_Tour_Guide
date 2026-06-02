import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  Compass,
  Landmark,
  Map as MapIcon,
  MessageSquare,
  Navigation,
  Volume2,
  WifiOff
} from 'lucide-react';
import MapExplore from '../map/MapExplore';
import UnifiedChatPage from '../voice/UnifiedChatPage';
import LanguageToggle from '../shared/LanguageToggle';

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
    lat: artifact.lat,
    lng: artifact.lng,
    raw: artifact
  };
};

const ArtifactDetailPanel = ({
  artifact,
  language,
  onAsk,
  onShowMap
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
      </div>

      <section className="artifact-summary-block">
        <span>{isVi ? 'Tóm tắt' : 'Summary'}</span>
        <p>
          {artifact.summary || (isVi
            ? 'Thông tin chi tiết sẽ xuất hiện sau khi bạn yêu cầu AI giới thiệu hoặc đặt câu hỏi về điểm dừng này.'
            : 'Details will appear after you ask the AI guide to introduce this stop or ask a related question.')}
        </p>
      </section>

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
  const [activeTab, setActiveTab] = useState(location.initialTab || 'map');
  const [targetArtifact, setTargetArtifact] = useState(null);
  const [currentArtifact, setCurrentArtifact] = useState(null);
  const [systemPrompt, setSystemPrompt] = useState(null);
  const [routeStatus, setRouteStatus] = useState(null);
  const [isOnline, setIsOnline] = useState(() => (
    typeof navigator === 'undefined' ? true : navigator.onLine
  ));

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

        <LanguageToggle language={language} setLanguage={setLanguage} />
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
            embedded
          />
        </section>

        <section className={`tour-shell-panel artifact-panel-mobile ${activeTab === 'artifact' ? 'is-active' : ''}`}>
          <ArtifactDetailPanel
            artifact={normalizedArtifact}
            language={language}
            onAsk={handleAskArtifact}
            onShowMap={() => setActiveTab('map')}
          />
        </section>
      </main>

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
    </div>
  );
};

export default ExploreDashboard;
