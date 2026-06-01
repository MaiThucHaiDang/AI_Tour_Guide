import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Polygon, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { LocateFixed, Navigation, MapPin, Info, CheckCircle, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Volume2, Wrench, Save, RefreshCw, Compass, X, Play } from 'lucide-react';
import { playTTS, getMapConfigAPI, saveMapConfigAPI } from '../../services/apiService';

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Icons
const CurrentLocationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Helper function to return beautiful custom 2.5D architecture icons
const getCustomIcon = (artifactId, isTarget = false) => {
  // Mapping each specific monument ID to its real-world structured icon
  const iconNames = {
    1: 'cua_hoa_binh.png',  // Cửa Hòa Bình
    2: 'kien_trung.png',     // Điện Kiến Trung
    3: 'truong_sanh.png',    // Cung Trường Sanh
    4: 'dien_tho.png',       // Cung Diên Thọ
    5: 'chuong_duc.png',     // Cửa Chương Đức
    6: 'hung_mieu.png',      // Hưng Miếu
    7: 'the_mieu.png',       // Thế Miếu
    8: 'thai_hoa.png',       // Điện Thái Hòa
    9: 'can_chanh.png',      // Nền điện Cần Chánh
    10: 'theater.png',        // Duyệt Thị Đường
    11: 'palace.png',         // Phủ Nội Vụ
    12: 'garden.png',         // Vườn Cơ Hạ
    13: 'hung_mieu.png',      // Triệu Miếu (giống Hưng Miếu)
    14: 'the_mieu.png',       // Thái Miếu (giống Thế Miếu)
    15: 'gate.png',           // Cửa Hiển Nhơn
    16: 'palace.png',         // Điện Long An
    17: 'ngo_mon.png'         // Ngọ Môn
  };
  
  const iconName = iconNames[artifactId] || 'palace.png';
  const size = isTarget ? 58 : 46;
  return new L.Icon({
    iconUrl: `/assets/icons/${iconName}`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [size, size],
    iconAnchor: [size / 2, size - 2],
    popupAnchor: [0, -size + 10],
    shadowSize: [size, size]
  });
};

const MapClickHandler = ({ onMapClick }) => {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng);
    },
  });
  return null;
};

const MapCenterer = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      const targetZoom = map.getZoom() < 16 ? 16 : map.getZoom();
      map.setView(center, targetZoom, { animate: true });
    }
  }, [center, map]);
  return null;
};

// Hoàng Thành Huế (Đại Nội) Boundary coordinates for Polygon
const IMPERIAL_CITY_BOUNDARY = [
  [16.469447, 107.581697], // Đông Nam
  [16.465889, 107.576669], // Tây Nam
  [16.470200, 107.573342], // Tây Bắc
  [16.473720, 107.578359]  // Đông Bắc
];

// Kinh thành Huế: 17 công trình
const HUE_ARTIFACTS = [
  { id: 1,  name_vi: "Cửa Hòa Bình",                    name_en: "Hoa Binh Gate",              lat: 16.4721279, lng: 107.5762716 },
  { id: 2,  name_vi: "Điện Kiến Trung",                  name_en: "Kien Trung Palace",          lat: 16.4710479, lng: 107.5765559 },
  { id: 3,  name_vi: "Cung Trường Sanh",                 name_en: "Truong Sanh Palace",         lat: 16.469725,  lng: 107.574694  },
  { id: 4,  name_vi: "Cung Diên Thọ",                    name_en: "Dien Tho Palace",            lat: 16.4688556, lng: 107.5753417 },
  { id: 5,  name_vi: "Cửa Chương Đức",                   name_en: "Chuong Duc Gate",            lat: 16.4673314, lng: 107.5757295 },
  { id: 6,  name_vi: "Hưng Miếu",                        name_en: "Hung Mieu Temple",           lat: 16.4674263, lng: 107.5764189 },
  { id: 7,  name_vi: "Thế Miếu",                         name_en: "The Mieu Temple",            lat: 16.4671621, lng: 107.5767333 },
  { id: 8,  name_vi: "Điện Thái Hòa",                    name_en: "Thai Hoa Palace",            lat: 16.4686747, lng: 107.578412  },
  { id: 9,  name_vi: "Nền điện Cần Chánh",               name_en: "Can Chanh Palace Foundation", lat: 16.4695281, lng: 107.5777743 },
  { id: 10, name_vi: "Duyệt Thị Đường",                  name_en: "Duyet Thi Duong Theater",    lat: 16.470284,  lng: 107.5785163 },
  { id: 11, name_vi: "Phủ Nội Vụ",                       name_en: "Phu Nội Vụ",                 lat: 16.470755,  lng: 107.5796368 },
  { id: 12, name_vi: "Vườn Cơ Hạ",                       name_en: "Co Ha Garden",               lat: 16.4717727, lng: 107.5788666 },
  { id: 13, name_vi: "Triệu Miếu",                       name_en: "Trieu Mieu Temple",          lat: 16.4701907, lng: 107.5801058 },
  { id: 14, name_vi: "Thái Miếu",                        name_en: "Thai Mieu Temple",           lat: 16.4699109, lng: 107.5803246 },
  { id: 15, name_vi: "Cửa Hiển Nhơn",                    name_en: "Hien Nhon Gate",             lat: 16.4707473, lng: 107.5805514 },
  { id: 16, name_vi: "Điện Long An (Bảo tàng Cổ vật)",   name_en: "Long An Palace (Museum)",    lat: 16.4712819, lng: 107.5818602 },
  { id: 17, name_vi: "Ngọ Môn",                          name_en: "Ngo Mon Gate (Meridian Gate)", lat: 16.467766,  lng: 107.579146  },
];

const MAP_BOUNDS = [
  [16.4625, 107.5706], // SW
  [16.4765, 107.5854]  // NE
];

// Helper to calculate distance in meters between two points
const getDistance = (p1, p2) => {
  if (!p1 || !p2) return 0;
  const R = 6371000; // Radius of the Earth in meters
  const dLat = (p2.lat - p1.lat) * Math.PI / 180;
  const dLng = (p2.lng - p1.lng) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(p1.lat * Math.PI / 180) * Math.cos(p2.lat * Math.PI / 180) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const MapExplore = ({ onBack, onNavigateToStorytelling, onInstructionUpdate, language, embedded = false }) => {
  const isVi = language === 'vi';
  
  const [showStartModal, setShowStartModal] = useState(true);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [targetLocation, setTargetLocation] = useState(null);
  const [routePath, setRoutePath] = useState([]);
  const [instructions, setInstructions] = useState([]);
  const [isNavigating, setIsNavigating] = useState(false);
  const [isNavigatingStarted, setIsNavigatingStarted] = useState(false);
  const [isManualMode, setIsManualMode] = useState(false);
  const [useGPS, setUseGPS] = useState(false);
  const lastRouteStartRef = React.useRef(null);
  const [mapCenter, setMapCenter] = useState(null);
  const [mapBounds, setMapBounds] = useState(MAP_BOUNDS);
  const [artifactsList, setArtifactsList] = useState(HUE_ARTIFACTS);
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [isStepsExpanded, setIsStepsExpanded] = useState(false);
  const [isTooFarFromHue, setIsTooFarFromHue] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [statusType, setStatusType] = useState('success');

  // Fetch latest calibrated config from DB on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await getMapConfigAPI();
        if (data.success) {
          setMapBounds(data.map_bounds);
          setArtifactsList(data.artifacts);
        }
      } catch (err) {
        console.error('Failed to load map config in MapExplore:', err);
      }
    };
    fetchConfig();
  }, []);

  // GPS watch tracking effect
  useEffect(() => {
    if (!isNavigatingStarted || !useGPS || !targetLocation) return;

    let watchId = null;
    if ("geolocation" in navigator) {
      watchId = navigator.geolocation.watchPosition(
        (position) => {
          const loc = { lat: position.coords.latitude, lng: position.coords.longitude };
          setCurrentLocation(loc);
          setMapCenter([loc.lat, loc.lng]);
          
          // Re-calculate route if user moves > 8 meters from last route calculation start point
          const dist = getDistance(loc, lastRouteStartRef.current);
          if (dist > 8) {
            calculateRoute(loc, targetLocation);
          }
        },
        (error) => {
          console.error("GPS Watch error:", error);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    }

    return () => {
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
      }
    };
  }, [isNavigatingStarted, useGPS, targetLocation]);

  const getArtifactName = (art) => isVi ? art.name_vi : art.name_en;

  const handleGetGPS = () => {
    setIsManualMode(false);
    setShowStartModal(false);
    setUseGPS(true);
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc = { lat: position.coords.latitude, lng: position.coords.longitude };
          setCurrentLocation(loc);
          setMapCenter([loc.lat, loc.lng]);
        },
        (error) => {
          console.error("GPS error:", error);
          const center = { lat: 16.4695, lng: 107.5780 };
          setCurrentLocation(center);
          setMapCenter([center.lat, center.lng]);
        }
      );
    }
  };

  const handleChooseOnMap = () => {
    setIsManualMode(true);
    setUseGPS(false);
    setShowStartModal(false);
  };

  const handleMapClick = (latlng) => {
    if (isManualMode || !currentLocation) {
      const loc = { lat: latlng.lat, lng: latlng.lng };
      setCurrentLocation(loc);
      setIsManualMode(false);
      setUseGPS(false);
      if (isNavigating && targetLocation) {
        calculateRoute(loc, targetLocation);
      }
    }
  };

  const handleGoToNgoMon = () => {
    setMapCenter([16.467766, 107.579146]);
  };

  const handleRelocateGPS = () => {
    setIsManualMode(false);
    setUseGPS(true);
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc = { lat: position.coords.latitude, lng: position.coords.longitude };
          setCurrentLocation(loc);
          setMapCenter([loc.lat, loc.lng]);
          if (isNavigating && targetLocation) calculateRoute(loc, targetLocation);
        },
        () => {}
      );
    }
  };

  const handleRelocateManual = () => {
    setIsManualMode(true);
    setUseGPS(false);
  };

  const startNavigation = async (artifact) => {
    setTargetLocation(artifact);
    setIsNavigating(true);
    setIsNavigatingStarted(false);
    if (currentLocation) {
      await calculateRoute(currentLocation, artifact);
    }
  };

  const calculateRoute = async (start, end) => {
    try {
      const distToHue = Math.sqrt(Math.pow(start.lat - 16.4695, 2) + Math.pow(start.lng - 107.5780, 2));
      setIsTooFarFromHue(distToHue > 0.05);

      const url = `/api/v1/map/route?start_lat=${start.lat}&start_lng=${start.lng}&end_lat=${end.lat}&end_lng=${end.lng}&lang=${language}`;
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success && data.instructions.length > 0) {
        setRoutePath(data.coordinates);
        setInstructions(data.instructions);
        setActiveStepIndex(0);
        setIsStepsExpanded(false);
        lastRouteStartRef.current = start;
        
        if (onInstructionUpdate) {
          const name = getArtifactName(end);
          const fullGuide = isVi 
            ? `Lộ trình đi bộ từ vị trí của bạn đến ${name}: ${data.instructions.join(' ')}`
            : `Walking directions from your location to ${name}: ${data.instructions.join(' ')}`;
          onInstructionUpdate(fullGuide);
        }
      } else {
        throw new Error(data.message || "Failed to find walking route");
      }
    } catch (error) {
      console.error("Failed to calculate route:", error);
      setRoutePath([[start.lat, start.lng], [end.lat, end.lng]]);
      const fallbackText = isVi 
        ? `Đi thẳng đến ${getArtifactName(end)}` 
        : `Walk straight to ${getArtifactName(end)}`;
      setInstructions([fallbackText]);
      setActiveStepIndex(0);
      setIsStepsExpanded(false);
      lastRouteStartRef.current = start;
    }
  };

  const handleArrived = () => {
    if (targetLocation) {
      setCurrentLocation({ lat: targetLocation.lat, lng: targetLocation.lng });
      setMapCenter([targetLocation.lat, targetLocation.lng]);
    }
    setIsNavigating(false);
    setIsNavigatingStarted(false);
    setRoutePath([]);
    setInstructions([]);
    setActiveStepIndex(0);
    setIsStepsExpanded(false);
    if (onNavigateToStorytelling && targetLocation) {
      onNavigateToStorytelling(targetLocation);
    }
  };

  const handleCancelNavigation = () => {
    setIsNavigating(false);
    setIsNavigatingStarted(false);
    setTargetLocation(null);
    setRoutePath([]);
    setInstructions([]);
    setActiveStepIndex(0);
    setIsStepsExpanded(false);
  };

  const handleStartNavigation = () => {
    setIsNavigatingStarted(true);
    if (instructions.length > 0) {
      playTTS(instructions[0], language);
    }
  };

  const handleIntroduce = (artifact) => {
    if (onNavigateToStorytelling) {
      onNavigateToStorytelling(artifact);
    }
  };

  const handleNextStep = () => {
    if (activeStepIndex < instructions.length - 1) {
      const nextIdx = activeStepIndex + 1;
      setActiveStepIndex(nextIdx);
      playTTS(instructions[nextIdx], language);
    }
  };

  const handlePrevStep = () => {
    if (activeStepIndex > 0) {
      const prevIdx = activeStepIndex - 1;
      setActiveStepIndex(prevIdx);
      playTTS(instructions[prevIdx], language);
    }
  };

  const handleSpeakActiveStep = () => {
    if (instructions[activeStepIndex]) {
      playTTS(instructions[activeStepIndex], language);
    }
  };

  const handleSelectStep = (idx) => {
    setActiveStepIndex(idx);
    playTTS(instructions[idx], language);
  };

  const handleBoundsChange = (corner, field, val) => {
    const numVal = parseFloat(val);
    if (isNaN(numVal)) return;
    setMapBounds(prev => {
      const next = [ [...prev[0]], [...prev[1]] ];
      if (corner === 'sw') {
        if (field === 'lat') next[0][0] = numVal;
        else next[0][1] = numVal;
      } else {
        if (field === 'lat') next[1][0] = numVal;
        else next[1][1] = numVal;
      }
      return next;
    });
  };

  const showStatus = (msg, type = 'success') => {
    setStatusMessage(msg);
    setStatusType(type);
    setTimeout(() => {
      setStatusMessage(null);
    }, 4500);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const res = await saveMapConfigAPI(mapBounds, artifactsList);
      if (res.success) {
        showStatus(isVi ? 'Đã lưu cấu hình vào Database và file dự phòng thành công!' : 'Saved map configuration to DB and backup file successfully!', 'success');
      }
    } catch (err) {
      console.error('Failed to save config in MapExplore:', err);
      showStatus(isVi ? 'Lỗi khi lưu cấu hình.' : 'Failed to save configuration.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const getExportedToado = () => {
    return artifactsList.map(art => `${art.name_vi}: ${art.lat.toFixed(7)}, ${art.lng.toFixed(7)} (Xem trên bản đồ)`).join('\n');
  };

  const getExportedCode = () => {
    return JSON.stringify(artifactsList.map(art => ({
      id: art.id,
      name_vi: art.name_vi,
      name_en: art.name_en,
      lat: parseFloat(art.lat.toFixed(7)),
      lng: parseFloat(art.lng.toFixed(7))
    })), null, 2);
  };

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      {/* Status Notification Toast */}
      {statusMessage && (
        <div style={{
          position: 'absolute', top: '20px', left: '50%', transform: 'translateX(-50%)', zIndex: 3000,
          backgroundColor: statusType === 'success' ? '#d4edda' : '#f8d7da',
          color: statusType === 'success' ? '#155724' : '#721c24',
          border: `1px solid ${statusType === 'success' ? '#c3e6cb' : '#f5c6cb'}`,
          padding: '10px 20px', borderRadius: '10px', fontSize: '13px', fontWeight: '600',
          boxShadow: '0 4px 15px rgba(0,0,0,0.15)', textAlign: 'center'
        }}>
          {statusMessage}
        </div>
      )}
      
      {/* Start Modal */}
      {showStartModal && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 2000,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div style={{
            background: '#fff', borderRadius: '20px', padding: '32px 28px',
            maxWidth: '380px', width: '90%', textAlign: 'center',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
          }}>
            <div style={{
              width: '60px', height: '60px', borderRadius: '16px',
              background: 'linear-gradient(135deg, #0f5f59, #1a8a7e)',
              display: 'grid', placeItems: 'center', margin: '0 auto 16px'
            }}>
              <MapPin size={30} color="#fff" />
            </div>
            <h3 style={{ margin: '0 0 8px', fontSize: '20px', fontWeight: '700', color: '#1a1a1a' }}>
              {isVi ? 'Xác định vị trí của bạn' : 'Set your location'}
            </h3>
            <p style={{ margin: '0 0 24px', fontSize: '14px', color: '#666', lineHeight: '1.5' }}>
              {isVi 
                ? 'Chọn cách xác định vị trí hiện tại để bắt đầu khám phá Kinh thành Huế'
                : 'Choose how to set your current position to start exploring the Hue Imperial City'}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button onClick={handleGetGPS} style={{
                padding: '14px 20px', borderRadius: '12px', border: 'none',
                background: 'linear-gradient(135deg, #2196f3, #1976d2)',
                color: '#fff', fontWeight: '600', fontSize: '15px',
                cursor: 'pointer', display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: '10px',
                boxShadow: '0 4px 15px rgba(33,150,243,0.3)'
              }}>
                <LocateFixed size={20} />
                {isVi ? 'Định vị GPS tự động' : 'Auto GPS Location'}
              </button>
              <button onClick={handleChooseOnMap} style={{
                padding: '14px 20px', borderRadius: '12px',
                border: '2px solid #e0e0e0', background: '#fff',
                color: '#333', fontWeight: '600', fontSize: '15px',
                cursor: 'pointer', display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: '10px'
              }}>
                <MapPin size={20} />
                {isVi ? 'Chọn vị trí trên bản đồ' : 'Pick on map'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Controls */}
      {!showStartModal && (
        <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 1000, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button onClick={handleGoToNgoMon} title={isVi ? 'Về Ngọ Môn (Cổng chính)' : 'Go to Ngo Mon Gate'} style={{
            width: '45px', height: '45px', borderRadius: '12px',
            backgroundColor: '#ff9800', color: '#fff',
            border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}>
            <Compass size={22} />
          </button>
          <button onClick={handleRelocateGPS} title={isVi ? 'Định vị GPS' : 'GPS Locate'} style={{
            width: '45px', height: '45px', borderRadius: '12px',
            backgroundColor: '#2196f3', color: '#fff',
            border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}>
            <LocateFixed size={22} />
          </button>
          <button onClick={handleRelocateManual} title={isVi ? 'Chọn vị trí trên bản đồ' : 'Pick on map'} style={{
            width: '45px', height: '45px', borderRadius: '12px',
            backgroundColor: isManualMode ? '#f44336' : '#fff',
            color: isManualMode ? '#fff' : '#666',
            border: '1px solid #ddd', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}>
            <MapPin size={22} />
          </button>
          <button onClick={() => setIsCalibrating(!isCalibrating)} title={isVi ? 'Mở chế độ căn chỉnh' : 'Calibration Mode'} style={{
            width: '45px', height: '45px', borderRadius: '12px',
            backgroundColor: isCalibrating ? '#0f5f59' : '#fff',
            color: isCalibrating ? '#fff' : '#0f5f59',
            border: '1px solid #0f5f59', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}>
            <Wrench size={22} />
          </button>
        </div>
      )}

      {/* Manual mode hint */}
      {isManualMode && !showStartModal && (
        <div style={{
          position: 'absolute', top: '20px', left: '50%', transform: 'translateX(-50%)',
          zIndex: 1000, backgroundColor: 'rgba(244,67,54,0.9)', color: '#fff',
          padding: '10px 20px', borderRadius: '12px', fontSize: '13px', fontWeight: '600',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)', pointerEvents: 'none'
        }}>
          {isVi ? '👆 Chạm vào bản đồ để chọn vị trí của bạn' : '👆 Tap the map to set your location'}
        </div>
      )}

      {/* Map Calibration Panel */}
      {isCalibrating && !showStartModal && (
        <div style={{
          position: 'absolute', top: '20px', left: '20px', zIndex: 1001,
          width: '320px', backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)',
          borderRadius: '16px', padding: '16px', boxShadow: '0 8px 30px rgba(0,0,0,0.2)',
          maxHeight: '85%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: '#0f5f59' }}>
              {isVi ? '🔧 Căn Chỉnh Bản Đồ' : '🔧 Map Calibration'}
            </h3>
            <button onClick={() => setIsCalibrating(false)} style={{
              background: 'none', border: 'none', cursor: 'pointer', color: '#999', fontWeight: 'bold'
            }}>✕</button>
          </div>

          <p style={{ margin: 0, fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
            {isVi 
              ? 'Kéo thả các chấm đỏ trên bản đồ để cập nhật tọa độ công trình. Chỉnh bounds góc Tây Nam (SW) và Đông Bắc (NE) bên dưới để co giãn ảnh bản đồ.'
              : 'Drag red markers to change monument coordinates. Adjust SouthWest (SW) and NorthEast (NE) bounds to stretch the map image.'}
          </p>

          <button onClick={handleSave} disabled={isSaving} style={{
            padding: '10px 14px', borderRadius: '10px', border: 'none',
            background: 'linear-gradient(135deg, #4caf50, #388e3c)',
            color: '#fff', fontWeight: '700', fontSize: '13px',
            cursor: isSaving ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: '8px', boxShadow: '0 4px 12px rgba(76,175,80,0.2)',
            width: '100%'
          }}>
            {isSaving ? <RefreshCw className="spin" size={15} /> : <Save size={15} />}
            {isVi ? 'LƯU VÀO DATABASE' : 'SAVE TO DATABASE'}
          </button>

          <div>
            <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', fontWeight: '600' }}>MAP_BOUNDS</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
              <div>
                <label style={{ fontSize: '10px', color: '#888' }}>SW Lat</label>
                <input type="number" step="0.00001" value={mapBounds[0][0]} onChange={(e) => handleBoundsChange('sw', 'lat', e.target.value)} style={{ width: '100%', padding: '6px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
              </div>
              <div>
                <label style={{ fontSize: '10px', color: '#888' }}>SW Lng</label>
                <input type="number" step="0.00001" value={mapBounds[0][1]} onChange={(e) => handleBoundsChange('sw', 'lng', e.target.value)} style={{ width: '100%', padding: '6px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '10px', color: '#888' }}>NE Lat</label>
                <input type="number" step="0.00001" value={mapBounds[1][0]} onChange={(e) => handleBoundsChange('ne', 'lat', e.target.value)} style={{ width: '100%', padding: '6px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
              </div>
              <div>
                <label style={{ fontSize: '10px', color: '#888' }}>NE Lng</label>
                <input type="number" step="0.00001" value={mapBounds[1][1]} onChange={(e) => handleBoundsChange('ne', 'lng', e.target.value)} style={{ width: '100%', padding: '6px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
              </div>
            </div>
          </div>

          <div>
            <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', fontWeight: '600' }}>
              {isVi ? 'Xuất toado.md' : 'Export toado.md'}
            </h4>
            <textarea readOnly value={getExportedToado()} style={{ width: '100%', height: '80px', fontSize: '11px', padding: '6px', borderRadius: '6px', border: '1px solid #ccc', resize: 'vertical', fontFamily: 'monospace' }} />
          </div>

          <div>
            <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', fontWeight: '600' }}>
              {isVi ? 'Xuất HUE_ARTIFACTS (code)' : 'Export HUE_ARTIFACTS'}
            </h4>
            <textarea readOnly value={getExportedCode()} style={{ width: '100%', height: '100px', fontSize: '11px', padding: '6px', borderRadius: '6px', border: '1px solid #ccc', resize: 'vertical', fontFamily: 'monospace' }} />
          </div>
        </div>
      )}

      {/* Leaflet Map Container */}
      <MapContainer 
        bounds={mapBounds} 
        style={{ height: '100%', width: '100%' }} 
        zoomControl={false}
        maxZoom={19}
        minZoom={14}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polygon 
          positions={IMPERIAL_CITY_BOUNDARY} 
          pathOptions={{
            color: '#DAA520',
            fillColor: '#FFD700',
            fillOpacity: 0.08,
            weight: 3,
            dashArray: '5, 5'
          }}
        />
        <MapClickHandler onMapClick={handleMapClick} />
        {mapCenter && <MapCenterer center={mapCenter} />}

        {/* Current location marker */}
        {currentLocation && (
          <Marker position={[currentLocation.lat, currentLocation.lng]} icon={CurrentLocationIcon}>
            <Popup>{isVi ? 'Vị trí của bạn' : 'Your position'}</Popup>
          </Marker>
        )}

        {/* Artifact markers */}
        {artifactsList.map(art => (
          <Marker 
            key={art.id} 
            position={[art.lat, art.lng]} 
            icon={getCustomIcon(art.id, targetLocation?.id === art.id)}
            draggable={isCalibrating}
            eventHandlers={{
              dragend: (e) => {
                const marker = e.target;
                const position = marker.getLatLng();
                setArtifactsList(prev => prev.map(item => 
                  item.id === art.id 
                    ? { ...item, lat: position.lat, lng: position.lng }
                    : item
                ));
              }
            }}
          >
            <Popup>
              <div style={{ textAlign: 'center', minWidth: '200px' }}>
                <h3 style={{ margin: '0 0 4px', fontSize: '15px', fontWeight: '700', color: '#1a1a1a' }}>
                  {getArtifactName(art)}
                </h3>
                <p style={{ margin: '0 0 12px', fontSize: '11px', color: '#888' }}>
                  {isVi ? art.name_en : art.name_vi}
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <button onClick={() => startNavigation(art)} style={{
                    padding: '8px 14px', backgroundColor: '#2196f3', color: 'white',
                    border: 'none', borderRadius: '8px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                    fontSize: '13px', fontWeight: '600'
                  }}>
                    <Navigation size={14} />
                    {isVi ? 'Chỉ đường đến đây' : 'Navigate here'}
                  </button>
                  <button onClick={() => handleIntroduce(art)} style={{
                    padding: '8px 14px', backgroundColor: '#0f5f59', color: 'white',
                    border: 'none', borderRadius: '8px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                    fontSize: '13px', fontWeight: '600'
                  }}>
                    <Info size={14} />
                    {isVi ? 'Giới thiệu' : 'Introduce'}
                  </button>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {routePath.length > 0 && (
          <Polyline 
            positions={routePath} 
            pathOptions={{ color: '#2196f3', weight: 6, opacity: 0.8 }} 
          />
        )}
      </MapContainer>

      {/* Navigation Panel */}
      {isNavigating && targetLocation && (
        <div style={{
          position: 'absolute', bottom: '20px', left: '20px', right: '20px',
          backgroundColor: 'white', padding: '16px', borderRadius: '16px',
          boxShadow: '0 8px 30px rgba(0,0,0,0.18)', zIndex: 1000,
          maxHeight: '380px', display: 'flex', flexDirection: 'column', gap: '12px'
        }}>
          {!isNavigatingStarted ? (
            /* ─── Route Overview (Bước trung gian) ─── */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '40px', height: '40px', borderRadius: '12px',
                  background: 'linear-gradient(135deg, #2196f3, #1565c0)',
                  display: 'grid', placeItems: 'center', flexShrink: 0
                }}>
                  <Navigation size={20} color="#fff" />
                </div>
                <div>
                  <h4 style={{ margin: 0, color: '#1976d2', fontSize: '15px', fontWeight: '700' }}>
                    {isVi ? 'Tổng quan lộ trình đến' : 'Route overview to'}
                  </h4>
                  <p style={{ margin: 0, fontSize: '14px', color: '#333', fontWeight: '600' }}>
                    {getArtifactName(targetLocation)}
                  </p>
                </div>
              </div>

              {isTooFarFromHue && (
                <div style={{
                  backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffeeba',
                  padding: '10px', borderRadius: '8px', fontSize: '11px', lineHeight: '1.4'
                }}>
                  {isVi 
                    ? '⚠️ Bạn đang ở ngoài khu vực Hoàng thành Huế. Lộ trình vẽ đường chim bay để tham khảo. Bạn nên ghim vị trí bắt đầu gần di tích.'
                    : '⚠️ You are outside Hue Citadel area. A straight line is drawn for reference.'}
                </div>
              )}

              <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
                {isVi 
                  ? `Lộ trình bao gồm ${instructions.length} bước chỉ dẫn đi bộ.` 
                  : `Route contains ${instructions.length} walking steps.`}
              </p>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={handleCancelNavigation} style={{
                  flex: 1, padding: '12px', border: 'none', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '14px',
                  background: 'linear-gradient(135deg, #e0e0e0, #bdbdbd)',
                  color: '#333', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '8px',
                  boxShadow: '0 4px 10px rgba(0,0,0,0.08)'
                }}>
                  <X size={18} />
                  {isVi ? 'Hủy' : 'Cancel'}
                </button>
                <button onClick={handleStartNavigation} style={{
                  flex: 2, padding: '12px', border: 'none', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '14px',
                  background: 'linear-gradient(135deg, #2196f3, #1976d2)',
                  color: 'white', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '8px',
                  boxShadow: '0 4px 15px rgba(33,150,243,0.3)'
                }}>
                  <Play size={18} />
                  {isVi ? 'Bắt đầu' : 'Start'}
                </button>
              </div>
            </div>
          ) : (
            /* ─── Active Navigation Mode (Đang dẫn đường chi tiết) ─── */
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '10px',
                    background: 'linear-gradient(135deg, #2196f3, #1565c0)',
                    display: 'grid', placeItems: 'center', flexShrink: 0
                  }}>
                    <Navigation size={18} color="#fff" />
                  </div>
                  <div>
                    <h4 style={{ margin: 0, color: '#1976d2', fontSize: '15px', fontWeight: '700' }}>
                      {isVi ? 'Đang dẫn đường đi bộ đến' : 'Walking to'}
                    </h4>
                    <p style={{ margin: 0, fontSize: '13px', color: '#333', fontWeight: '500' }}>
                      {getArtifactName(targetLocation)}
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    onClick={() => setIsStepsExpanded(!isStepsExpanded)} 
                    style={{
                      padding: '6px 12px', borderRadius: '8px', border: '1px solid #ddd',
                      backgroundColor: isStepsExpanded ? '#f0f4f8' : '#fff', color: '#1976d2',
                      fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: '4px'
                    }}
                  >
                    {isStepsExpanded ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                    {isVi ? 'Toàn bộ bước' : 'All steps'}
                  </button>
                </div>
              </div>

              {isTooFarFromHue && (
                <div style={{
                  backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffeeba',
                  padding: '10px', borderRadius: '8px', fontSize: '11px', lineHeight: '1.4'
                }}>
                  {isVi 
                    ? '⚠️ Bạn đang ở ngoài khu vực Hoàng thành Huế. Định tuyến đã vẽ đường thẳng để tham khảo. Bạn nên ghim vị trí (nút 📍 ở góc trên phải) ngay trong Đại Nội để thử định tuyến đường đi bộ thực tế.'
                    : '⚠️ You are currently outside Hue Imperial City. Try placing your position manually (📍 button in top-right) inside the Citadel for walking route routing.'}
                </div>
              )}

              {instructions.length > 0 && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  backgroundColor: '#f8f9fa', padding: '12px', borderRadius: '12px',
                  border: '1px solid #e9ecef'
                }}>
                  <button 
                    onClick={handlePrevStep} 
                    disabled={activeStepIndex === 0}
                    style={{
                      padding: '6px', borderRadius: '8px', border: 'none',
                      backgroundColor: activeStepIndex === 0 ? '#e9ecef' : '#2196f3',
                      color: activeStepIndex === 0 ? '#999' : '#fff',
                      cursor: activeStepIndex === 0 ? 'not-allowed' : 'pointer',
                      display: 'grid', placeItems: 'center'
                    }}
                  >
                    <ChevronLeft size={16} />
                  </button>

                  <div style={{ flex: 1, fontSize: '13px', fontWeight: '500', color: '#333' }}>
                    <span style={{ color: '#1976d2', fontWeight: '700', marginRight: '6px' }}>
                      {isVi ? `Bước ${activeStepIndex + 1}/${instructions.length}:` : `Step ${activeStepIndex + 1}/${instructions.length}:`}
                    </span>
                    {instructions[activeStepIndex]}
                  </div>

                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button 
                      onClick={handleSpeakActiveStep}
                      title={isVi ? 'Đọc lại' : 'Speak'}
                      style={{
                        padding: '6px', borderRadius: '8px', border: '1px solid #ddd',
                        backgroundColor: '#fff', color: '#333', cursor: 'pointer',
                        display: 'grid', placeItems: 'center'
                      }}
                    >
                      <Volume2 size={16} />
                    </button>
                    
                    <button 
                      onClick={handleNextStep} 
                      disabled={activeStepIndex === instructions.length - 1}
                      style={{
                        padding: '6px', borderRadius: '8px', border: 'none',
                        backgroundColor: activeStepIndex === instructions.length - 1 ? '#e9ecef' : '#2196f3',
                        color: activeStepIndex === instructions.length - 1 ? '#999' : '#fff',
                        cursor: activeStepIndex === instructions.length - 1 ? 'not-allowed' : 'pointer',
                        display: 'grid', placeItems: 'center'
                      }}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}

              {isStepsExpanded && instructions.length > 0 && (
                <div style={{
                  flex: 1, overflowY: 'auto', padding: '4px',
                  borderLeft: '2px solid #e9ecef', marginLeft: '12px', paddingLeft: '16px'
                }}>
                  {instructions.map((instr, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => handleSelectStep(idx)}
                      style={{
                        position: 'relative', paddingBottom: '12px', cursor: 'pointer',
                        opacity: idx === activeStepIndex ? 1 : 0.6,
                        transition: 'opacity 0.2s'
                      }}
                    >
                      <div style={{
                        position: 'absolute', left: '-22px', top: '2px',
                        width: '10px', height: '10px', borderRadius: '50%',
                        backgroundColor: idx === activeStepIndex ? '#2196f3' : '#ccc',
                        border: idx === activeStepIndex ? '2px solid #fff' : 'none',
                        boxShadow: idx === activeStepIndex ? '0 0 0 2px #2196f3' : 'none'
                      }} />
                      
                      <p style={{
                        margin: 0, fontSize: '12px', 
                        fontWeight: idx === activeStepIndex ? '700' : '400',
                        color: idx === activeStepIndex ? '#1976d2' : '#555'
                      }}>
                        {idx + 1}. {instr}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={handleCancelNavigation} style={{
                  flex: 1, padding: '12px', border: 'none', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '14px',
                  background: 'linear-gradient(135deg, #f44336, #d32f2f)',
                  color: 'white', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '8px',
                  boxShadow: '0 4px 15px rgba(244,67,54,0.2)'
                }}>
                  <X size={18} />
                  {isVi ? 'Hủy' : 'Cancel'}
                </button>
                <button onClick={handleArrived} style={{
                  flex: 2, padding: '12px', border: 'none', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '14px',
                  background: 'linear-gradient(135deg, #4caf50, #388e3c)',
                  color: 'white', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '8px',
                  boxShadow: '0 4px 15px rgba(76,175,80,0.3)'
                }}>
                  <CheckCircle size={18} />
                  {isVi ? 'Đã đến & Giới thiệu' : 'Arrived & Introduce'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default MapExplore;
