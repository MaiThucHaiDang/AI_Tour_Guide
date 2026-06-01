import React, { useState, useEffect } from 'react';
import MapExplore from '../map/MapExplore';
import UnifiedChatPage from '../voice/UnifiedChatPage';
import { ArrowLeft, Maximize2, Minimize2, Map as MapIcon, MessageSquare } from 'lucide-react';

const ExploreDashboard = ({ onBack, language, setLanguage, initialLocation }) => {
  const [isMapExpanded, setIsMapExpanded] = useState(true);
  const [targetArtifact, setTargetArtifact] = useState(null);
  const [systemPrompt, setSystemPrompt] = useState(null);

  const handleNavigateToStorytelling = (artifact) => {
    setTargetArtifact(artifact);
    // When arriving, maybe shift focus to chat on mobile
    if (window.innerWidth < 768) {
      setIsMapExpanded(false);
    }
  };

  const handleMapInstruction = (text) => {
    setSystemPrompt(text);
  };

  return (
    <div className="explore-dashboard" style={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: '100vh', 
      width: '100vw', 
      overflow: 'hidden',
      backgroundColor: '#f0f2f5'
    }}>
      {/* Header Bar */}
      <div style={{
        height: '60px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        zIndex: 2000,
        boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <button onClick={onBack} style={{ 
            background: 'none', 
            border: 'none', 
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            color: '#1a1a1a'
          }}>
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
              {initialLocation?.name_vi || 'Khám phá'}
            </h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
              AI Tour Guide Dashboard
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              onClick={() => setIsMapExpanded(!isMapExpanded)}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid #ddd',
                backgroundColor: '#fff',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer'
              }}
            >
              {isMapExpanded ? <MessageSquare size={18} /> : <MapIcon size={18} />}
              <span style={{ fontSize: '14px' }}>
                {isMapExpanded ? (language === 'vi' ? 'Xem Chat' : 'View Chat') : (language === 'vi' ? 'Xem Bản đồ' : 'View Map')}
              </span>
            </button>
        </div>
      </div>

      {/* Content Wrapper */}
      <div style={{
        display: 'flex',
        flex: 1,
        flexDirection: window.innerWidth < 768 ? 'column' : 'row',
        width: '100%',
        height: 'calc(100% - 60px)',
        overflow: 'hidden'
      }}>
        {/* Map Section */}
        <div style={{ 
          flex: isMapExpanded ? 1.5 : 1, 
          position: 'relative',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          height: window.innerWidth < 768 ? (isMapExpanded ? '70%' : '30%') : '100%'
        }}>
          <MapExplore 
            onBack={onBack} 
            onNavigateToStorytelling={handleNavigateToStorytelling}
            onInstructionUpdate={handleMapInstruction}
            language={language}
            embedded={true}
          />
        </div>

        {/* Chat Section */}
        <div style={{ 
          flex: isMapExpanded ? 1 : 1.5,
          backgroundColor: '#fff',
          borderLeft: '1px solid #e0e0e0',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          height: window.innerWidth < 768 ? (isMapExpanded ? '30%' : '70%') : '100%',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <UnifiedChatPage 
            onBack={onBack}
            language={language}
            setLanguage={setLanguage}
            initialArtifact={targetArtifact}
            externalPrompt={systemPrompt}
            embedded={true}
          />
        </div>
      </div>
    </div>
  );
};

export default ExploreDashboard;
