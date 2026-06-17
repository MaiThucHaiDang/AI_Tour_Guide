import { MapPin, RotateCcw, Volume2 } from 'lucide-react';

const ChatContextStrip = ({
  currentArtifact,
  language,
  onResetContext,
  onListenIntro,
  onShowMap
}) => {
  const isVi = language === 'vi';
  if (!currentArtifact) return null;

  const imageUrl = currentArtifact.images?.[0] || currentArtifact.image || null;

  return (
    <div className="chat-context-strip">
      <div className="chat-context-info">
        {imageUrl ? (
          <img src={imageUrl} alt="" className="context-thumbnail" />
        ) : (
          <MapPin size={16} className="context-pin-icon" />
        )}
        <span className="context-label">
          {isVi ? 'Đang hỏi về:' : 'Asking about:'}
        </span>
        <strong className="context-name">{currentArtifact.name}</strong>
      </div>
      
      <div className="chat-context-actions">
        {onListenIntro && (
          <button 
            className="context-action-btn listen-btn" 
            onClick={() => onListenIntro(currentArtifact)}
            title={isVi ? 'Nghe giới thiệu' : 'Hear intro'}
          >
            <Volume2 size={14} />
            <span>{isVi ? 'Nghe giới thiệu' : 'Intro'}</span>
          </button>
        )}
        
        {onShowMap && (
          <button 
            className="context-action-btn map-btn" 
            onClick={onShowMap}
            title={isVi ? 'Đổi điểm trên bản đồ' : 'Change stop on map'}
          >
            <MapPin size={14} />
            <span>{isVi ? 'Đổi điểm' : 'Change stop'}</span>
          </button>
        )}

        {onResetContext && (
          <button 
            className="context-action-btn clear-btn" 
            onClick={onResetContext}
            title={isVi ? 'Xóa ngữ cảnh' : 'Clear context'}
          >
            <RotateCcw size={14} />
            <span>{isVi ? 'Xóa' : 'Clear'}</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatContextStrip;
