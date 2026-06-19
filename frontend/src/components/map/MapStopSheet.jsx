import React, { useState } from 'react';
import { Navigation, Volume2, MessageSquare, Camera, X, Clock, Ticket, Calendar, User } from 'lucide-react';
import { hasPhotoBoothFrame } from '../../data/photoBoothFrames';
import ImageGallery from '../shared/ImageGallery';

const MapStopSheet = ({
  artifact,
  language,
  onAsk,
  onAskAI,
  onNavigate,
  onPhotoBooth,
  onClose,
  currentLocation
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isVi = language === 'vi';

  if (!artifact) return null;

  const getDistanceText = () => {
    if (!currentLocation || !artifact.lat || !artifact.lng) return '';
    // Haversine formula
    const R = 6371e3; // metres
    const phi1 = currentLocation.lat * Math.PI / 180;
    const phi2 = artifact.lat * Math.PI / 180;
    const deltaPhi = (artifact.lat - currentLocation.lat) * Math.PI / 180;
    const deltaLambda = (artifact.lng - currentLocation.lng) * Math.PI / 180;

    const a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
              Math.cos(phi1) * Math.cos(phi2) *
              Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    const d = R * c; // in metres
    if (d < 1000) {
      return `${Math.round(d)}m`;
    }
    return `${(d / 1000).toFixed(1)}km`;
  };

  const distance = getDistanceText();
  const title = isVi
    ? artifact.nameVi || artifact.name_vi || artifact.name || ''
    : artifact.nameEn || artifact.name_en || artifact.name || '';
  const subtitle = isVi
    ? artifact.nameEn || artifact.name_en || ''
    : artifact.nameVi || artifact.name_vi || '';
  const highlight = isVi
    ? artifact.highlightVi || artifact.highlight_vi || ''
    : artifact.highlightEn || artifact.highlight_en || '';
  const summary = artifact.summary || (isVi ? 'Nhấn "Nghe giới thiệu" hoặc "Hỏi AI" để biết thêm thông tin.' : 'Tap "Hear intro" or "Ask AI" to learn more.');
  const hasPhotoFrame = hasPhotoBoothFrame(artifact.id);

  return (
    <div 
      className={`map-stop-sheet-container ${isExpanded ? 'expanded' : 'collapsed'}`}
      onClick={(e) => e.stopPropagation()}
      onPointerDown={(e) => e.stopPropagation()}
    >
      {/* Pull tab handle */}
      <div 
        className="sheet-drag-handle" 
        onClick={() => setIsExpanded(!isExpanded)}
        aria-label={isExpanded ? (isVi ? 'Thu nhỏ' : 'Collapse') : (isVi ? 'Mở rộng' : 'Expand')}
        role="button"
      >
        <span className="drag-indicator"></span>
      </div>

      {/* Header section (Always visible) */}
      <div className="sheet-header">
        <div className="sheet-header-main" onClick={() => setIsExpanded(!isExpanded)}>
          <div className="sheet-title-row">
            <h3>{title}</h3>
            {distance && <span className="sheet-distance-tag">{distance}</span>}
          </div>
          <p className="sheet-subtitle">{subtitle}</p>
        </div>
        
        <button className="sheet-close-btn" onClick={onClose} aria-label={isVi ? 'Đóng' : 'Close'}>
          <X size={18} />
        </button>
      </div>

      {/* Collapsed quick actions */}
      {!isExpanded && (
        <div className="sheet-collapsed-content">
          <button className="sheet-detail-hint" type="button" onClick={() => setIsExpanded(true)}>
            {isVi ? 'Nhấn vào để xem chi tiết' : 'Tap to view details'}
          </button>
          <div className="sheet-quick-actions">
            <button className="sheet-btn-primary" onClick={() => onAsk(artifact.raw || artifact)}>
              <Volume2 size={16} />
              <span>{isVi ? 'Nghe giới thiệu' : 'Hear intro'}</span>
            </button>
            <button className="sheet-btn-secondary" onClick={() => onAskAI(artifact.raw || artifact)}>
              <MessageSquare size={16} />
              <span>{isVi ? 'Hỏi AI' : 'Ask AI'}</span>
            </button>
            {onPhotoBooth && (
              <button
                className={`sheet-btn-secondary sheet-btn-checkin ${hasPhotoFrame ? '' : 'disabled'}`}
                onClick={() => hasPhotoFrame && onPhotoBooth(artifact.raw || artifact)}
                disabled={!hasPhotoFrame}
                title={hasPhotoFrame ? (isVi ? 'Check-in ảnh' : 'Photo check-in') : (isVi ? 'Khung sắp có' : 'No photo frame')}
              >
                <Camera size={16} />
                <span>{hasPhotoFrame ? (isVi ? 'Check-in' : 'Check-in') : (isVi ? 'Sắp có' : 'Soon')}</span>
              </button>
            )}
            <button className="sheet-btn-secondary icon-only" onClick={onNavigate} title={isVi ? 'Chỉ đường' : 'Route'}>
              <Navigation size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Expanded details */}
      {isExpanded && (
        <div className="sheet-expanded-content">
          {artifact.images && artifact.images.length > 0 && (
            <div className="sheet-gallery-container">
              <ImageGallery images={artifact.images} className="sheet-image-gallery" />
            </div>
          )}

          {highlight && (
            <div className="sheet-highlight-box">
              <span className="sheet-section-title">{isVi ? 'Điểm đặc sắc' : 'Highlight'}</span>
              <p>{highlight}</p>
            </div>
          )}

          <div className="sheet-details-grid">
            {artifact.year && (
              <div className="sheet-detail-item">
                <Calendar size={14} className="detail-icon" />
                <div>
                  <span>{isVi ? 'Năm dựng' : 'Year'}</span>
                  <strong>{artifact.year}</strong>
                </div>
              </div>
            )}
            {artifact.author && (
              <div className="sheet-detail-item">
                <User size={14} className="detail-icon" />
                <div>
                  <span>{isVi ? 'Tác giả / Triều đại' : 'Dynasty'}</span>
                  <strong>{artifact.author}</strong>
                </div>
              </div>
            )}
            {artifact.openHoursVi && (
              <div className="sheet-detail-item full-width">
                <Clock size={14} className="detail-icon" />
                <div>
                  <span>{isVi ? 'Giờ mở cửa' : 'Open Hours'}</span>
                  <strong>{isVi ? artifact.openHoursVi : artifact.openHoursEn}</strong>
                </div>
              </div>
            )}
            {artifact.ticketVi && (
              <div className="sheet-detail-item full-width">
                <Ticket size={14} className="detail-icon" />
                <div>
                  <span>{isVi ? 'Giá vé' : 'Ticket'}</span>
                  <strong>{isVi ? artifact.ticketVi : artifact.ticketEn}</strong>
                </div>
              </div>
            )}
          </div>

          <div className="sheet-summary-box">
            <span className="sheet-section-title">{isVi ? 'Tóm tắt' : 'Summary'}</span>
            <p>{summary}</p>
          </div>

          <div className="sheet-full-actions">
            <button className="sheet-action-btn primary" onClick={() => onAsk(artifact.raw || artifact)}>
              <Volume2 size={18} />
              <span>{isVi ? 'Nghe giới thiệu' : 'Hear intro'}</span>
            </button>
            <button className="sheet-action-btn secondary" onClick={() => onAskAI(artifact.raw || artifact)}>
              <MessageSquare size={18} />
              <span>{isVi ? 'Hỏi AI' : 'Ask AI'}</span>
            </button>
            <button className="sheet-action-btn secondary" onClick={onNavigate}>
              <Navigation size={18} />
              <span>{isVi ? 'Chỉ đường' : 'Route'}</span>
            </button>
            {onPhotoBooth && (
              <button 
                className={`sheet-action-btn checkin ${hasPhotoFrame ? '' : 'disabled'}`} 
                onClick={() => hasPhotoFrame && onPhotoBooth(artifact.raw || artifact)}
                disabled={!hasPhotoFrame}
              >
                <Camera size={18} />
                <span>{hasPhotoFrame ? (isVi ? 'Check-in ảnh' : 'Photo check-in') : (isVi ? 'Khung sắp có' : 'No photo frame')}</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapStopSheet;
