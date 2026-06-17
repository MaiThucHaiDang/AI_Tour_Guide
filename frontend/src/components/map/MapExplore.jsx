import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Polygon, CircleMarker, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import { LocateFixed, Navigation, MapPin, Info, CheckCircle, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Volume2, Pause, Wrench, Save, RefreshCw, Compass, X, Play, Route, Camera, Lock } from 'lucide-react';
import { playTTS, stopTTS, pauseTTS, resumeTTS, isTTSPaused, getMapConfigAPI, getRouteAPI, saveMapConfigAPI, planTourAPI } from '../../services/apiService';
import ImageGallery from '../shared/ImageGallery';
import { hasPhotoBoothFrame } from '../../data/photoBoothFrames';

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// Trusted Types policy helper to support Leaflet DivIcon HTML in secure environments
let leafletTrustedPolicy;
if (typeof window !== 'undefined' && window.trustedTypes && window.trustedTypes.createPolicy) {
  if (window.__leafletTrustedPolicy) {
    leafletTrustedPolicy = window.__leafletTrustedPolicy;
  } else {
    try {
      leafletTrustedPolicy = window.trustedTypes.createPolicy('leaflet-policy', {
        createHTML: (string) => string
      });
      window.__leafletTrustedPolicy = leafletTrustedPolicy;
    } catch (e) {
      console.warn("Trusted Types policy creation failed:", e);
    }
  }
}

const getTrustedHTML = (htmlString) => {
  if (leafletTrustedPolicy) {
    return leafletTrustedPolicy.createHTML(htmlString);
  }
  return htmlString;
};

// Custom Icons
const CurrentLocationIcon = new L.DivIcon({
  html: getTrustedHTML('<span class="current-location-marker" aria-hidden="true"></span>'),
  className: 'current-location-div-icon',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -16]
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
    shadowUrl: markerShadow,
    iconSize: [size, size],
    iconAnchor: [size / 2, size - 2],
    popupAnchor: [0, -size + 10],
    shadowSize: [size, size]
  });
};

const getNumberedIcon = (number, isActive = false) => {
  const bgColor = isActive ? '#0f5f59' : '#DAA520';
  const border = isActive ? '3px solid #fff' : '2px solid #fff';
  const scale = isActive ? 'scale(1.1)' : 'scale(1.0)';
  const shadow = 'box-shadow: 0 4px 10px rgba(0,0,0,0.35);';
  const htmlContent = `<div style="background-color: ${bgColor}; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; border: ${border}; ${shadow} transform: ${scale}; transition: all 0.2s;">${number}</div>`;
  
  return new L.DivIcon({
    html: getTrustedHTML(htmlContent),
    className: 'custom-numbered-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15]
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

const MapInstanceCapture = ({ setMapInstance }) => {
  const map = useMap();
  useEffect(() => {
    if (map) {
      setMapInstance(map);
    }
  }, [map, setMapInstance]);
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

const OPEN_HOURS_VI = "Mùa hè (16/03-15/10): 06:30-18:00\nMùa đông (16/10-15/03): 07:00-17:30";
const OPEN_HOURS_EN = "Summer (Mar 16-Oct 15): 06:30-18:00\nWinter (Oct 16-Mar 15): 07:00-17:30";

const TICKET_HUE_VI = "Người lớn: 200.000 VNĐ\nTrẻ em (7-12 tuổi): 40.000 VNĐ\nTrẻ em dưới 7 tuổi: Miễn phí";
const TICKET_HUE_EN = "Adult: 200,000 VND\nChildren (7-12): 40,000 VND\nUnder 7: Free";

const TICKET_MUSEUM_VI = "Người lớn: 50.000 VNĐ\nTrẻ em dưới 12 tuổi: Miễn phí";
const TICKET_MUSEUM_EN = "Adult: 50,000 VND\nChildren under 12: Free";

// Kinh thành Huế: 17 công trình
export const HUE_ARTIFACTS = [
  { id: 1,  name_vi: "Cửa Hòa Bình",                    name_en: "Hoa Binh Gate",              lat: 16.4721279, lng: 107.5762716, highlightVi: "Cổng phía Bắc của Tử Cấm Thành, nổi bật với nghệ thuật khảm sành sứ tinh xảo.", highlightEn: "Northern gate of the Forbidden City, featuring exquisite porcelain mosaic art.", images: ["/assets/images/art_1_1.jpg", "/assets/images/art_1_2.jpg"] },
  { id: 2,  name_vi: "Điện Kiến Trung",                  name_en: "Kien Trung Palace",          lat: 16.4710479, lng: 107.5765559, highlightVi: "Cung điện mang phong cách kết hợp Á - Âu độc đáo, nơi sinh hoạt của vua Bảo Đại.", highlightEn: "Unique Asian-European fusion palace, residence of Emperor Bao Dai.", images: ["/assets/images/art_2_1.jpg", "/assets/images/art_2_2.jpg"] },
  { id: 3,  name_vi: "Cung Trường Sanh",                 name_en: "Truong Sanh Palace",         lat: 16.469725,  lng: 107.574694,  highlightVi: "Khu nghỉ dưỡng thanh tĩnh dành cho Hoàng Thái Hậu với cảnh quan sân vườn đẹp.", highlightEn: "Peaceful retreat for the Empress Dowager with beautiful garden landscape.", images: ["/assets/images/art_3_1.jpg", "/assets/images/art_3_2.jpg"] },
  { id: 4,  name_vi: "Cung Diên Thọ",                    name_en: "Dien Tho Palace",            lat: 16.4688556, lng: 107.5753417, highlightVi: "Nơi ở của Hoàng Thái Hậu, quần thể cung điện lớn và nguyên vẹn nhất Đại Nội.", highlightEn: "Residence of the Empress Dowager, the largest and most intact palace complex in the Citadel.", images: ["/assets/images/art_4_1.jpg", "/assets/images/art_4_2.jpg"] },
  { id: 5,  name_vi: "Cửa Chương Đức",                   name_en: "Chuong Duc Gate",            lat: 16.4673314, lng: 107.5757295, highlightVi: "Cổng phía Tây Tử Cấm Thành, mang kiến trúc cung đình đặc trưng triều Nguyễn.", highlightEn: "Western gate of the Forbidden City, featuring typical Nguyen court architecture.", images: ["/assets/images/art_5_1.jpg", "/assets/images/art_5_2.jpg"] },
  { id: 6,  name_vi: "Hưng Miếu",                        name_en: "Hung Mieu Temple",           lat: 16.4674263, lng: 107.5764189, highlightVi: "Thờ thân phụ vua Gia Long, thể hiện sự tôn kính nguồn gốc hoàng tộc Nguyễn.", highlightEn: "Shrine to Emperor Gia Long's father, honoring the Nguyen dynasty's origins.", images: ["/assets/images/art_6_1.jpg", "/assets/images/art_6_2.jpg"] },
  { id: 7,  name_vi: "Thế Miếu",                         name_en: "The Mieu Temple",            lat: 16.4671621, lng: 107.5767333, highlightVi: "Nơi thờ các vị vua triều Nguyễn và lưu giữ bộ Cửu Đỉnh nổi tiếng.", highlightEn: "Shrine to Nguyen emperors, housing the famous Nine Dynastic Urns.", images: ["/assets/images/art_7_1.jpg", "/assets/images/art_7_2.jpg"] },
  { id: 8,  name_vi: "Điện Thái Hòa",                    name_en: "Thai Hoa Palace",            lat: 16.4686747, lng: 107.578412,  highlightVi: "Trung tâm quyền lực của triều Nguyễn, nơi tổ chức các đại lễ và lễ đăng quang.", highlightEn: "Power center of the Nguyen dynasty, venue for grand ceremonies and coronations.", images: ["/assets/images/art_8_1.jpg", "/assets/images/art_8_2.jpg"] },
  { id: 9,  name_vi: "Nền điện Cần Chánh",               name_en: "Can Chanh Palace Foundation", lat: 16.4695281, lng: 107.5777743, highlightVi: "Dấu tích điện làm việc của nhà vua, gợi nhớ kiến trúc cung điện đã mất.", highlightEn: "Remains of the king's working palace, evoking lost palace architecture.", images: ["/assets/images/art_9_1.jpg", "/assets/images/art_9_2.jpg"] },
  { id: 10, name_vi: "Duyệt Thị Đường",                  name_en: "Duyet Thi Duong Theater",    lat: 16.470284,  lng: 107.5785163, highlightVi: "Nhà hát cung đình cổ nhất Việt Nam, nơi biểu diễn Nhã nhạc cung đình Huế.", highlightEn: "Vietnam's oldest royal theater, venue for Hue royal court music.", images: ["/assets/images/art_10_1.jpg", "/assets/images/art_10_2.jpg"] },
  { id: 11, name_vi: "Phủ Nội Vụ",                       name_en: "Phu Noi Vu",                 lat: 16.470755,  lng: 107.5796368, highlightVi: "Cơ quan quản lý tài sản và đồ dùng của Hoàng gia triều Nguyễn.", highlightEn: "Agency managing royal assets and supplies of the Nguyen dynasty.", images: ["/assets/images/art_11_1.jpg", "/assets/images/art_11_2.jpg"] },
  { id: 12, name_vi: "Vườn Cơ Hạ",                       name_en: "Co Ha Garden",               lat: 16.4717727, lng: 107.5788666, highlightVi: "Ngự uyển nổi tiếng với kiến trúc sân vườn và không gian thư giãn của vua.", highlightEn: "Famous royal garden with landscape architecture and the king's relaxation space.", images: ["/assets/images/art_12_1.jpg", "/assets/images/art_12_2.jpg"] },
  { id: 13, name_vi: "Triệu Miếu",                       name_en: "Trieu Mieu Temple",          lat: 16.4701907, lng: 107.5801058, highlightVi: "Thờ Nguyễn Kim, vị tiền tổ có công đặt nền móng cho họ Nguyễn.", highlightEn: "Shrine to Nguyen Kim, the ancestor who laid the foundation for the Nguyen clan.", images: ["/assets/images/art_13_1.jpg", "/assets/images/art_13_2.jpg"] },
  { id: 14, name_vi: "Thái Miếu",                        name_en: "Thai Mieu Temple",           lat: 16.4699109, lng: 107.5803246, highlightVi: "Công trình thờ tự các chúa Nguyễn, có giá trị lịch sử và kiến trúc cao.", highlightEn: "Shrine to the Nguyen lords, of great historical and architectural value.", images: ["/assets/images/art_14_1.jpg", "/assets/images/art_14_2.jpg"] },
  { id: 15, name_vi: "Cửa Hiển Nhơn",                    name_en: "Hien Nhon Gate",             lat: 16.4707473, lng: 107.5805514, highlightVi: "Cổng phía Đông Hoàng Thành, nổi tiếng với nghệ thuật chạm khắc gỗ tinh tế.", highlightEn: "Eastern gate of the Imperial City, famous for intricate wood carving art.", images: ["/assets/images/art_15_1.jpg", "/assets/images/art_15_2.jpg"] },
  { id: 16, name_vi: "Điện Long An (Bảo tàng Cổ vật)",   name_en: "Long An Palace (Museum)",    lat: 16.4712819, lng: 107.5818602, openHoursVi: OPEN_HOURS_VI, openHoursEn: OPEN_HOURS_EN, ticketVi: TICKET_MUSEUM_VI, ticketEn: TICKET_MUSEUM_EN, highlightVi: "Hiện là Bảo tàng Cổ vật Cung đình Huế, lưu giữ nhiều hiện vật quý triều Nguyễn.", highlightEn: "Now the Hue Royal Antiquities Museum, preserving precious Nguyen artifacts.", images: ["/assets/images/art_16_1.jpg", "/assets/images/art_16_2.jpg"] },
  { id: 17, name_vi: "Ngọ Môn",                          name_en: "Ngo Mon Gate (Meridian Gate)", lat: 16.467734,  lng: 107.579151,  openHoursVi: OPEN_HOURS_VI, openHoursEn: OPEN_HOURS_EN, ticketVi: TICKET_HUE_VI, ticketEn: TICKET_HUE_EN, highlightVi: "Cổng chính của Hoàng Thành Huế, biểu tượng kiến trúc nổi tiếng nhất của Đại Nội.", highlightEn: "Main gate of Hue Imperial City, the most iconic architectural symbol of the Citadel.", images: ["/assets/images/art_17_1.jpg", "/assets/images/art_17_2.jpg"] },
];

const MAP_BOUNDS = [
  [16.4625, 107.5706], // SW
  [16.4765, 107.5854]  // NE
];

const isValidArtifactPosition = (artifact, bounds = MAP_BOUNDS) => {
  const lat = Number(artifact?.lat);
  const lng = Number(artifact?.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return false;
  if (lat === 0 && lng === 0) return false;
  const safeBounds = Array.isArray(bounds)
    && bounds.length === 2
    && Array.isArray(bounds[0])
    && Array.isArray(bounds[1])
    ? bounds
    : MAP_BOUNDS;
  const [[swLat, swLng], [neLat, neLng]] = safeBounds;
  const padding = 0.003;
  return (
    lat >= Math.min(swLat, neLat) - padding
    && lat <= Math.max(swLat, neLat) + padding
    && lng >= Math.min(swLng, neLng) - padding
    && lng <= Math.max(swLng, neLng) + padding
  );
};

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

// Generate arrow markers along a path
const getPathArrows = (path, spacing = 4) => {
  if (!path || path.length < 4) return [];
  const arrows = [];
  let accumulated = 0;
  for (let i = 1; i < path.length; i++) {
    const prev = path[i - 1];
    const curr = path[i];
    const segDist = getDistance({ lat: prev[0], lng: prev[1] }, { lat: curr[0], lng: curr[1] });
    accumulated += segDist;
    if (accumulated >= spacing * (arrows.length + 1) * 15) {
      const angle = Math.atan2(curr[0] - prev[0], curr[1] - prev[1]) * 180 / Math.PI;
      arrows.push({ pos: curr, angle });
    }
  }
  return arrows;
};

const MapExplore = ({
  onNavigateToStorytelling,
  onOpenArtifactContext,
  onArtifactFocus,
  onRouteStatusChange,
  onPassportCheckIn,
  onPhotoBooth,
  language,
  embedded = false,
  visitorMode = false,
  active = true,
  externalNavigationTarget = null,
  onExternalNavigationConsumed = null,
  focusedArtifactId = null
}) => {
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
  const [selectedArtifact, setSelectedArtifact] = useState(null);

  // Smart Tour Planning States
  const [tourData, setTourData] = useState(null);
  const [activeTourIndex, setActiveTourIndex] = useState(0);
  const [isTourModalOpen, setIsTourModalOpen] = useState(false);
  const [tourDuration, setTourDuration] = useState(60);
  const [tourPlacesCount, setTourPlacesCount] = useState(5);
  const [isGeneratingTour, setIsGeneratingTour] = useState(false);
  
  // Map Leaflet Instance state to close popups programmatically
  const [mapInstance, setMapInstance] = useState(null);
  const [isStepPaused, setIsStepPaused] = useState(false);

  // Fetch latest calibrated config from DB on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await getMapConfigAPI();
        if (data.success) {
          setMapBounds(data.map_bounds);
          const merged = data.artifacts.map(art => {
            const local = HUE_ARTIFACTS.find(a => Number(a.id) === Number(art.id));
            return local ? { ...local, ...art } : art;
          }).filter(artifact => isValidArtifactPosition(artifact, data.map_bounds || MAP_BOUNDS));
          setArtifactsList(merged);
        }
      } catch (err) {
        console.error('Failed to load map config in MapExplore:', err);
      }
    };
    fetchConfig();
  }, []);

  const getArtifactName = useCallback((art) => (
    isVi ? art.name_vi : art.name_en
  ), [isVi]);

  const calculateRoute = useCallback(async (start, end) => {
    try {
      const distToHue = Math.sqrt(Math.pow(start.lat - 16.4695, 2) + Math.pow(start.lng - 107.5780, 2));
      const isFar = distToHue > 0.05;
      setIsTooFarFromHue(isFar);

      let finalStart = start;
      if (isFar) {
        // Fallback start coordinates to Ngọ Môn (ID 17) if user is too far from Hue
        finalStart = { lat: 16.467734, lng: 107.579151 };
        setCurrentLocation(finalStart);
      }

      const data = await getRouteAPI({ start: finalStart, end, lang: language });

      if (data.success && data.instructions.length > 0) {
        setRoutePath(data.coordinates);
        setInstructions(data.instructions);
        setActiveStepIndex(0);
        setIsStepsExpanded(false);
        lastRouteStartRef.current = start;


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
  }, [getArtifactName, isVi, language]);

  // GPS watch tracking effect (runs when GPS is enabled, handles both routing and passport check-in)
  useEffect(() => {
    if (!useGPS) return;

    let watchId = null;
    if ("geolocation" in navigator) {
      watchId = navigator.geolocation.watchPosition(
        (position) => {
          const loc = { lat: position.coords.latitude, lng: position.coords.longitude };
          setCurrentLocation(loc);
          setMapCenter([loc.lat, loc.lng]);

          // 1. Auto Check-in Logic (Proximity < 30m)
          if (onPassportCheckIn) {
            artifactsList.filter((artifact) => isValidArtifactPosition(artifact)).forEach(artifact => {
              const dist = getDistance(loc, artifact);
              if (dist < 30) {
                onPassportCheckIn(artifact, { method: 'gps', distanceMeters: dist });
              }
            });
          }

          // 2. Route Recalculation Logic
          if (isNavigatingStarted && targetLocation) {
            const distFromLastStart = getDistance(loc, lastRouteStartRef.current);
            if (distFromLastStart > 8) {
              calculateRoute(loc, targetLocation);
            }
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
  }, [artifactsList, calculateRoute, isNavigatingStarted, targetLocation, useGPS, onPassportCheckIn]);

  useEffect(() => {
    if (!onRouteStatusChange) return;
    onRouteStatusChange({
      isNavigating,
      isStarted: isNavigatingStarted,
      targetId: targetLocation?.id || null,
      targetName: targetLocation ? (isVi ? targetLocation.name_vi : targetLocation.name_en) : '',
      activeStep: activeStepIndex,
      totalSteps: instructions.length,
      currentInstruction: instructions[activeStepIndex] || '',
      isTooFarFromHue
    });
  }, [
    activeStepIndex,
    instructions,
    isNavigating,
    isNavigatingStarted,
    isTooFarFromHue,
    isVi,
    onRouteStatusChange,
    targetLocation
  ]);

  useEffect(() => {
    if (!active) return;
    const timeoutId = window.setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 80);
    return () => window.clearTimeout(timeoutId);
  }, [active]);

  useEffect(() => {
    if (!active || !focusedArtifactId) return;
    const focusedArtifact = artifactsList.find(artifact => Number(artifact.id) === Number(focusedArtifactId));
    if (focusedArtifact) {
      setSelectedArtifact(focusedArtifact);
      setMapCenter([focusedArtifact.lat, focusedArtifact.lng]);
    }
  }, [active, artifactsList, focusedArtifactId]);

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
    setMapCenter([16.467734, 107.579151]);
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
    setSelectedArtifact(artifact);
    onArtifactFocus?.(artifact);
    setMapCenter([artifact.lat, artifact.lng]);
    setTargetLocation(artifact);
    setIsNavigating(true);
    setIsNavigatingStarted(false);
    mapInstance?.closePopup();
    if (currentLocation) {
      await calculateRoute(currentLocation, artifact);
    }
  };

  const handleArrivedOnly = () => {
    if (targetLocation) {
      setCurrentLocation({ lat: targetLocation.lat, lng: targetLocation.lng });
      setMapCenter([targetLocation.lat, targetLocation.lng]);
    }
    
    // If a tour is active, increment the activeTourIndex so they can go to the next stop later
    if (tourData) {
      setActiveTourIndex(prev => prev + 1);
    }
    
    setIsNavigating(false);
    setIsNavigatingStarted(false);
    setRoutePath([]);
    setInstructions([]);
    setActiveStepIndex(0);
    setIsStepsExpanded(false);
  };

  const handleArrived = () => {
    if (targetLocation) {
      setCurrentLocation({ lat: targetLocation.lat, lng: targetLocation.lng });
      setMapCenter([targetLocation.lat, targetLocation.lng]);
    }
    
    // If a tour is active, increment the activeTourIndex so they can go to the next stop later
    if (tourData) {
      setActiveTourIndex(prev => prev + 1);
    }
    
    setIsNavigating(false);
    setIsNavigatingStarted(false);
    setRoutePath([]);
    setInstructions([]);
    setActiveStepIndex(0);
    setIsStepsExpanded(false);
    if (onNavigateToStorytelling && targetLocation) {
      onArtifactFocus?.(targetLocation);
      onNavigateToStorytelling(targetLocation);
    }
  };

  // Handle external navigation request (e.g. from recommended next stop)
  useEffect(() => {
    if (externalNavigationTarget && active) {
      const art = artifactsList.find(a => a.id === externalNavigationTarget.id);
      if (art) {
        startNavigation(art);
        onExternalNavigationConsumed?.();
      }
    }
  }, [externalNavigationTarget, active, artifactsList, onExternalNavigationConsumed]);

  const handleGenerateTour = async () => {
    let startLoc = currentLocation;
    if (!startLoc) {
      // Fallback start coordinates to Ngọ Môn (ID 17) if currentLocation is not set
      startLoc = { lat: 16.467734, lng: 107.579151 };
      setCurrentLocation(startLoc);
      setMapCenter([startLoc.lat, startLoc.lng]);
    }
    
    try {
      setIsGeneratingTour(true);
      const res = await planTourAPI({
        start: startLoc,
        maxDuration: tourDuration,
        maxPlaces: tourPlacesCount,
        lang: language
      });
      
      if (res.success) {
        setTourData(res);
        setActiveTourIndex(0);
        setIsTourModalOpen(false);
        
        const msg = isVi 
          ? `Lập lộ trình thành công! ${res.route.length} địa điểm trong ${res.total_duration} phút.`
          : `Route ready: ${res.route.length} stops in ${res.total_duration} mins.`;
        showStatus(msg, 'success');
        
        if (res.route.length > 0) {
          startTourDestination(res.route[0], 0);
        }
      } else {
        showStatus(res.message || (isVi ? 'Không thể tạo lộ trình.' : 'Could not generate tour.'), 'error');
      }
    } catch (err) {
      console.error('Failed to generate tour:', err);
      showStatus(isVi ? 'Lỗi kết nối khi tạo lộ trình.' : 'Network error generating tour.', 'error');
    } finally {
      setIsGeneratingTour(false);
    }
  };

  const handleCancelTour = () => {
    setTourData(null);
    setActiveTourIndex(0);
    setIsTourModalOpen(false);
    handleCancelNavigation();
    showStatus(isVi ? 'Đã hủy lộ trình đề xuất.' : 'Route cleared.', 'success');
  };

  const startTourDestination = async (artifact, index) => {
    setSelectedArtifact(artifact);
    onArtifactFocus?.(artifact);
    setMapCenter([artifact.lat, artifact.lng]);
    setTargetLocation(artifact);
    setIsNavigating(true);
    setIsNavigatingStarted(false);
    setActiveTourIndex(index);
    const startLoc = currentLocation || { lat: 16.467734, lng: 107.579151 };
    await calculateRoute(startLoc, artifact);
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
    setIsStepPaused(false);
    if (instructions.length > 0) {
      playTTS(instructions[0], language);
    }
  };

  const handleIntroduce = (artifact) => {
    setSelectedArtifact(artifact);
    onArtifactFocus?.(artifact);
    setMapCenter([artifact.lat, artifact.lng]);
    mapInstance?.closePopup();
    if (onNavigateToStorytelling) {
      onNavigateToStorytelling(artifact);
    }
  };

  const handleSelectArtifact = (artifact) => {
    setSelectedArtifact(artifact);
    onArtifactFocus?.(artifact);
    setMapCenter([artifact.lat, artifact.lng]);
  };

  const handleAskSelectedArtifact = (artifact) => {
    setSelectedArtifact(artifact);
    mapInstance?.closePopup();
    if (onOpenArtifactContext) {
      onOpenArtifactContext(artifact);
    } else if (onNavigateToStorytelling) {
      onNavigateToStorytelling(artifact);
    }
  };

  const handleNextStep = () => {
    if (activeStepIndex < instructions.length - 1) {
      stopTTS();
      setIsStepPaused(false);
      const nextIdx = activeStepIndex + 1;
      setActiveStepIndex(nextIdx);
      playTTS(instructions[nextIdx], language);
    }
  };

  const handlePrevStep = () => {
    if (activeStepIndex > 0) {
      stopTTS();
      setIsStepPaused(false);
      const prevIdx = activeStepIndex - 1;
      setActiveStepIndex(prevIdx);
      playTTS(instructions[prevIdx], language);
    }
  };

  const handleSpeakActiveStep = () => {
    if (isStepPaused) {
      resumeTTS();
      setIsStepPaused(false);
      return;
    }
    if (instructions[activeStepIndex]) {
      playTTS(instructions[activeStepIndex], language);
      setIsStepPaused(false);
    }
  };

  const handlePauseStep = () => {
    pauseTTS();
    setIsStepPaused(true);
  };

  const handleSelectStep = (idx) => {
    stopTTS();
    setIsStepPaused(false);
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
    <div className={`map-explore-surface ${embedded ? 'embedded-map' : ''}`} style={{ height: '100%', width: '100%', position: 'relative' }}>
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
        <div className="map-start-overlay">
          <div className="map-start-sheet" role="dialog" aria-modal="true">
            <div className="map-start-icon" aria-hidden="true">
              <MapPin size={30} />
            </div>
            <h3>
              {isVi ? 'Xác định vị trí của bạn' : 'Set your location'}
            </h3>
            <p>
              {isVi 
                ? 'Chọn cách xác định vị trí hiện tại để bắt đầu khám phá Kinh thành Huế'
                : 'Choose how to set your current position to start exploring the Hue Imperial City'}
            </p>
            <div className="map-start-actions">
              <button className="map-action-primary" onClick={handleGetGPS}>
                <LocateFixed size={20} />
                {isVi ? 'Định vị GPS tự động' : 'Auto GPS Location'}
              </button>
              <button className="map-action-secondary" onClick={handleChooseOnMap}>
                <MapPin size={20} />
                {isVi ? 'Chọn vị trí trên bản đồ' : 'Pick on map'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Controls */}
      {!showStartModal && (
        <div className="map-floating-controls">
          <button
            className="map-icon-button is-gold"
            onClick={handleGoToNgoMon}
            title={isVi ? 'Về Ngọ Môn (Cổng chính)' : 'Go to Ngo Mon Gate'}
            aria-label={isVi ? 'Về Ngọ Môn' : 'Go to Ngo Mon Gate'}
          >
            <Compass size={22} />
          </button>
          <button
            className="map-icon-button is-jade"
            onClick={handleRelocateGPS}
            title={isVi ? 'Định vị GPS' : 'GPS Locate'}
            aria-label={isVi ? 'Định vị GPS' : 'GPS Locate'}
          >
            <LocateFixed size={22} />
          </button>
          <button
            className={`map-icon-button ${isManualMode ? 'is-danger' : 'is-paper'}`}
            onClick={handleRelocateManual}
            title={isVi ? 'Chọn vị trí trên bản đồ' : 'Pick on map'}
            aria-label={isVi ? 'Chọn vị trí trên bản đồ' : 'Pick location on map'}
          >
            <MapPin size={22} />
          </button>
          <button
            className={`map-icon-button ${tourData ? 'is-jade' : 'is-paper'}`}
            onClick={() => setIsTourModalOpen(true)}
            title={isVi ? 'Gợi ý lộ trình' : 'Suggested route'}
            aria-label={isVi ? 'Gợi ý lộ trình' : 'Suggested route'}
          >
            <Route size={22} />
          </button>
          {!visitorMode && (
            <button
              className={`map-icon-button ${isCalibrating ? 'is-jade' : 'is-paper'}`}
              onClick={() => setIsCalibrating(!isCalibrating)}
              title={isVi ? 'Mở chế độ căn chỉnh' : 'Calibration Mode'}
              aria-label={isVi ? 'Mở chế độ căn chỉnh' : 'Open calibration mode'}
            >
              <Wrench size={22} />
            </button>
          )}
        </div>
      )}

      {/* Manual mode hint */}
      {isManualMode && !showStartModal && (
        <div className="map-manual-hint">
          {isVi ? 'Chạm vào bản đồ để chọn vị trí của bạn' : 'Tap the map to set your location'}
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
        preferCanvas
        wheelDebounceTime={80}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          keepBuffer={2}
          updateWhenIdle
          updateWhenZooming={false}
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
        <MapInstanceCapture setMapInstance={setMapInstance} />
        {mapCenter && <MapCenterer center={mapCenter} />}

        {/* Current location marker */}
        {currentLocation && (
          <Marker position={[currentLocation.lat, currentLocation.lng]} icon={CurrentLocationIcon}>
            <Popup>{isVi ? 'Vị trí của bạn' : 'Your position'}</Popup>
          </Marker>
        )}

        {/* Artifact markers */}
        {artifactsList.filter((artifact) => isValidArtifactPosition(artifact)).map(art => {
          const isFocused = Number(focusedArtifactId) === Number(art.id);
          const isActiveTarget = Number(targetLocation?.id) === Number(art.id);
          const routeIndex = tourData ? tourData.route.findIndex(item => item.id === art.id) : -1;
          return (
          <Marker 
            key={art.id} 
            position={[art.lat, art.lng]} 
            icon={routeIndex !== -1
              ? getNumberedIcon(routeIndex + 1, isActiveTarget || isFocused)
              : getCustomIcon(art.id, isActiveTarget || isFocused)
            }
            draggable={isCalibrating}
            eventHandlers={{
              click: (event) => {
                event.originalEvent?.stopPropagation?.();
                handleSelectArtifact(art);
              },
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
              <div className="artifact-popup">
                <h3>
                  {getArtifactName(art)}
                </h3>
                <p>
                  {isVi ? art.name_en : art.name_vi}
                </p>
                {art.images && art.images.length > 0 && (
                  <ImageGallery
                    images={art.images}
                    className="artifact-popup-gallery"
                    imgClassName="popup-gallery-img"
                    clipContainer=".leaflet-container"
                  />
                )}
                {art.highlightVi && (
                  <p className="artifact-popup-highlight">
                    {isVi ? art.highlightVi : art.highlightEn}
                  </p>
                )}
                {(art.id === 16 || art.id === 17) && art.openHoursVi && (
                  <div className="artifact-popup-info">
                    <div className="popup-info-row">
                      <span className="popup-info-label">{isVi ? 'Giờ mở cửa' : 'Open hours'}</span>
                      <span className="popup-info-value">{isVi ? art.openHoursVi : art.openHoursEn}</span>
                    </div>
                    <div className="popup-info-row">
                      <span className="popup-info-label">{isVi ? 'Giá vé' : 'Ticket'}</span>
                      <span className="popup-info-value">{isVi ? art.ticketVi : art.ticketEn}</span>
                    </div>
                  </div>
                )}
                <div className="artifact-popup-actions">
                  <button className="artifact-popup-primary" onClick={() => startNavigation(art)}>
                    <Navigation size={14} />
                    {isVi ? 'Chỉ đường đến đây' : 'Navigate here'}
                  </button>
                  <button className="artifact-popup-secondary" onClick={() => handleIntroduce(art)}>
                    <Info size={14} />
                    {isVi ? 'Nghe giới thiệu' : 'Hear intro'}
                  </button>
                  <button
                    className="artifact-popup-secondary"
                    onClick={() => hasPhotoBoothFrame(art.id) && onPhotoBooth?.(art)}
                    disabled={!hasPhotoBoothFrame(art.id)}
                    title={!hasPhotoBoothFrame(art.id) ? (isVi ? 'Khung check-in sẽ được bổ sung sau' : 'Photo frame coming later') : undefined}
                  >
                    {hasPhotoBoothFrame(art.id) ? <Camera size={14} /> : <Lock size={14} />}
                    {hasPhotoBoothFrame(art.id) ? (isVi ? 'Check-in ảnh' : 'Photo check-in') : (isVi ? 'Đang khóa' : 'Locked')}
                  </button>
                </div>
              </div>
            </Popup>
          </Marker>
          );
        })}

        {routePath.length > 0 && (
          <>
            {/* Glow layer */}
            <Polyline
              positions={routePath}
              pathOptions={{ color: '#1a73e8', weight: 20, opacity: 0.1, lineCap: 'round', lineJoin: 'round' }}
            />
            {/* Main blue route line (Google Maps style) */}
            <Polyline
              positions={routePath}
              pathOptions={{
                color: '#1a73e8',
                weight: 8,
                opacity: 0.92,
                lineCap: 'round',
                lineJoin: 'round',
                className: 'route-line-pulse'
              }}
            />
            {/* Inner lighter blue for dimension */}
            <Polyline
              positions={routePath}
              pathOptions={{
                color: '#89b4f8',
                weight: 3,
                opacity: 0.6,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
            {/* Arrows along the path */}
            {getPathArrows(routePath, 4).map((arrow, i) => (
              <Marker
                key={`arrow-${i}`}
                position={arrow.pos}
                icon={L.divIcon({
                  html: getTrustedHTML(`<div class="route-arrow-anim" style="transform: rotate(${arrow.angle}deg)"><span style="animation-delay: ${i * 0.15}s; color: #fff; text-shadow: 0 0 6px rgba(26,115,232,0.8);">▶</span></div>`),
                  className: 'route-arrow-icon',
                  iconSize: [20, 20],
                  iconAnchor: [10, 10]
                })}
                interactive={false}
              />
            ))}
            {/* Start marker */}
            {routePath[0] && (
              <CircleMarker
                center={routePath[0]}
                pathOptions={{ color: '#1a73e8', fillColor: '#fff', fillOpacity: 1, weight: 4 }}
                radius={8}
              />
            )}
            {/* End marker with pulse */}
            {routePath[routePath.length - 1] && (
              <>
                <CircleMarker
                  center={routePath[routePath.length - 1]}
                  pathOptions={{ color: '#e74c3c', fillColor: '#e74c3c', fillOpacity: 0.5, weight: 3 }}
                  radius={10}
                />
                <CircleMarker
                  center={routePath[routePath.length - 1]}
                  pathOptions={{ color: '#e74c3c', fillColor: '#e74c3c', fillOpacity: 0.15, weight: 1, className: 'route-end-pulse' }}
                  radius={16}
                />
              </>
            )}
          </>
        )}
      </MapContainer>

      {selectedArtifact && !isNavigating && !isTourModalOpen && !showStartModal && (
        <div
          className="map-context-card"
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => event.stopPropagation()}
        >
          <div className="map-context-copy">
            <span>{isVi ? 'Đang xem trên bản đồ' : 'Viewing on map'}</span>
            <strong>{getArtifactName(selectedArtifact)}</strong>
            <small>
              {isVi
                ? 'Chọn cách bạn muốn tiếp tục với điểm này.'
                : 'Choose how you want to continue from this stop.'}
            </small>
          </div>
          <div className="map-context-actions">
            <button onClick={() => handleIntroduce(selectedArtifact)}>
              <Volume2 size={15} />
              {isVi ? 'Nghe giới thiệu' : 'Hear intro'}
            </button>
            <button onClick={() => handleAskSelectedArtifact(selectedArtifact)}>
              <Info size={15} />
              {isVi ? 'Hỏi về điểm này' : 'Ask here'}
            </button>
            <button onClick={() => startNavigation(selectedArtifact)}>
              <Navigation size={15} />
              {isVi ? 'Đường đi' : 'Route'}
            </button>
            <button
              onClick={() => hasPhotoBoothFrame(selectedArtifact.id) && onPhotoBooth?.(selectedArtifact)}
              disabled={!hasPhotoBoothFrame(selectedArtifact.id)}
              title={!hasPhotoBoothFrame(selectedArtifact.id) ? (isVi ? 'Khung check-in sẽ được bổ sung sau' : 'Photo frame coming later') : undefined}
            >
              {hasPhotoBoothFrame(selectedArtifact.id) ? <Camera size={15} /> : <Lock size={15} />}
              {hasPhotoBoothFrame(selectedArtifact.id) ? (isVi ? 'Check-in ảnh' : 'Photo') : (isVi ? 'Khóa' : 'Locked')}
            </button>
          </div>
        </div>
      )}

      {/* Tour Planner Modal */}
      {isTourModalOpen && (
        <div className="map-start-overlay" style={{ zIndex: 3001 }}>
          <div className="map-start-sheet" style={{ maxWidth: '350px' }}>
            <div className="map-start-icon" style={{ background: 'linear-gradient(135deg, #0f5f59, #164c5e)' }}>
              <Route size={30} color="#fff" />
            </div>
            <h3>{isVi ? 'Gợi ý lộ trình' : 'Suggested route'}</h3>
            <p style={{ fontSize: '12px', color: '#666', marginTop: '-6px' }}>
              {isVi 
                ? 'Chọn thời gian và số điểm muốn ghé, app sẽ gợi ý một tuyến đi bộ phù hợp trong Đại Nội.'
                : 'Choose your time and number of stops, and the app will suggest a fitting walking route in the Citadel.'}
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', textAlign: 'left', margin: '10px 0' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: '#333', display: 'block', marginBottom: '6px' }}>
                  {isVi ? 'Quỹ thời gian của bạn:' : 'Your available time:'} <strong>{tourDuration} {isVi ? 'phút' : 'minutes'}</strong>
                </label>
                <input 
                  type="range" 
                  min="20" 
                  max="180" 
                  step="10" 
                  value={tourDuration} 
                  onChange={(e) => setTourDuration(parseInt(e.target.value))}
                  style={{ width: '100%', accentColor: '#0f5f59' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#888' }}>
                  <span>20m</span>
                  <span>60m</span>
                  <span>120m</span>
                  <span>180m</span>
                </div>
              </div>
              
              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: '#333', display: 'block', marginBottom: '6px' }}>
                  {isVi ? 'Số điểm tham quan tối đa:' : 'Max locations to visit:'}
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                  {[3, 5, 8, 10].map(num => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => setTourPlacesCount(num)}
                      style={{
                        padding: '6px',
                        borderRadius: '6px',
                        border: '1px solid',
                        borderColor: tourPlacesCount === num ? '#0f5f59' : '#ddd',
                        backgroundColor: tourPlacesCount === num ? '#edf5ef' : '#fff',
                        color: tourPlacesCount === num ? '#0f5f59' : '#333',
                        fontWeight: '700',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      {num}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', width: '100%', marginTop: '10px' }}>
              <button 
                className="map-action-secondary" 
                onClick={() => setIsTourModalOpen(false)}
                style={{ flex: 1, padding: '10px' }}
              >
                {isVi ? 'Đóng' : 'Close'}
              </button>
              {tourData && (
                <button 
                  className="map-action-secondary" 
                  onClick={handleCancelTour}
                  style={{ flex: 1, padding: '10px', backgroundColor: '#fff0f0', color: '#d32f2f', border: '1px solid #ffd2d2' }}
                >
                  {isVi ? 'Xóa lộ trình' : 'Clear route'}
                </button>
              )}
              <button 
                className="map-action-primary" 
                onClick={handleGenerateTour}
                disabled={isGeneratingTour}
                style={{ flex: 2, padding: '10px' }}
              >
                {isGeneratingTour ? (isVi ? 'Đang tạo...' : 'Planning...') : (isVi ? 'Tạo lộ trình' : 'Generate')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tour Progress bottom Panel */}
      {tourData && !isNavigating && (
        <div className="map-route-sheet" style={{ bottom: '20px', zIndex: 1000 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '12px',
                background: 'linear-gradient(135deg, #b2820a, #8c6003)',
                display: 'grid', placeItems: 'center', flexShrink: 0
              }}>
                <Compass size={20} color="#fff" />
              </div>
              <div>
                <h4 style={{ margin: 0, color: '#b2820a', fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {isVi ? 'Lộ trình đề xuất' : 'Suggested route'}
                </h4>
                <p style={{ margin: 0, fontSize: '14px', color: '#333', fontWeight: '600' }}>
                  {isVi 
                    ? `Đã hoàn thành ${activeTourIndex} / ${tourData.route.length} địa điểm`
                    : `Completed ${activeTourIndex} of ${tourData.route.length} stops`}
                </p>
              </div>
            </div>

            {activeTourIndex < tourData.route.length ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <p style={{ margin: 0, fontSize: '13px', color: '#666', lineHeight: '1.4' }}>
                  {isVi 
                    ? `Điểm tiếp theo trong lộ trình là: `
                    : `Next stop in your itinerary is: `}
                  <strong style={{ color: '#0f5f59' }}>
                    {getArtifactName(tourData.route[activeTourIndex])}
                  </strong>
                </p>
                
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button onClick={handleCancelTour} style={{
                    flex: 1, padding: '12px', border: 'none', borderRadius: '10px',
                    fontWeight: '700', cursor: 'pointer', fontSize: '13px',
                    background: 'linear-gradient(135deg, #e0e0e0, #bdbdbd)',
                    color: '#333', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', gap: '6px'
                  }}>
                    {isVi ? 'Hủy lộ trình' : 'Cancel route'}
                  </button>
                  <button 
                    onClick={() => startTourDestination(tourData.route[activeTourIndex], activeTourIndex)}
                    style={{
                      flex: 2, padding: '12px', border: 'none', borderRadius: '10px',
                      fontWeight: '700', cursor: 'pointer', fontSize: '13px',
                      background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                      color: 'white', display: 'flex', alignItems: 'center',
                      justifyContent: 'center', gap: '6px',
                      boxShadow: '0 4px 12px rgba(15,95,89,0.25)'
                    }}
                  >
                    <Navigation size={16} />
                    {isVi ? 'Đường đi chặng tiếp theo' : 'Start next leg'}
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <p style={{ margin: 0, fontSize: '13px', color: '#2e7d32', fontWeight: '600' }}>
                  🎉 {isVi 
                    ? 'Chúc mừng! Bạn đã hoàn thành toàn bộ lộ trình tham quan.' 
                    : 'Congratulations! You have completed the entire tour.'}
                </p>
                <button onClick={handleCancelTour} style={{
                  padding: '12px', border: 'none', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '13px',
                  background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                  color: 'white', width: '100%'
                }}>
                  {isVi ? 'Hoàn thành' : 'Done'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation Panel */}
      {isNavigating && targetLocation && (
        <div className="map-route-sheet">
          {!isNavigatingStarted ? (
            /* ─── Route Overview (Bước trung gian) ─── */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '40px', height: '40px', borderRadius: '12px',
                  background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                  display: 'grid', placeItems: 'center', flexShrink: 0
                }}>
                  <Navigation size={20} color="#fff" />
                </div>
                <div>
                  <h4 style={{ margin: 0, color: '#0f5f59', fontSize: '15px', fontWeight: '700' }}>
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
                    ? 'Bạn đang ở ngoài khu vực Hoàng thành Huế. Hãy ghim vị trí bắt đầu gần di tích để chỉ dẫn đi bộ chính xác hơn.'
                    : 'You are outside Hue Imperial City. Place your start point near the site for a more useful walking route.'}
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
                  background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
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
                    background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                    display: 'grid', placeItems: 'center', flexShrink: 0
                  }}>
                    <Navigation size={18} color="#fff" />
                  </div>
                  <div>
                    <h4 style={{ margin: 0, color: '#0f5f59', fontSize: '15px', fontWeight: '700' }}>
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
                      backgroundColor: isStepsExpanded ? '#edf5ef' : '#fff', color: '#0f5f59',
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
                    ? 'Bạn đang ở ngoài khu vực Hoàng thành Huế. Chọn lại vị trí trong Đại Nội để nhận chỉ dẫn đi bộ sát thực tế hơn.'
                    : 'You are outside Hue Imperial City. Pick a start point inside the Citadel for a more realistic walking route.'}
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
                      backgroundColor: activeStepIndex === 0 ? '#e9ecef' : '#0f5f59',
                      color: activeStepIndex === 0 ? '#999' : '#fff',
                      cursor: activeStepIndex === 0 ? 'not-allowed' : 'pointer',
                      display: 'grid', placeItems: 'center'
                    }}
                  >
                    <ChevronLeft size={16} />
                  </button>

                  <div style={{ flex: 1, fontSize: '13px', fontWeight: '500', color: '#333' }}>
                    <span style={{ color: '#0f5f59', fontWeight: '700', marginRight: '6px' }}>
                      {isVi ? `Bước ${activeStepIndex + 1}/${instructions.length}:` : `Step ${activeStepIndex + 1}/${instructions.length}:`}
                    </span>
                    {instructions[activeStepIndex]}
                  </div>

                  <div style={{ display: 'flex', gap: '6px' }}>
                    {isStepPaused ? (
                      <button 
                        onClick={handleSpeakActiveStep}
                        title={isVi ? 'Tiếp tục' : 'Resume'}
                        style={{
                          padding: '6px', borderRadius: '8px', border: '1px solid #0f5f59',
                          backgroundColor: '#edf5ef', color: '#0f5f59', cursor: 'pointer',
                          display: 'grid', placeItems: 'center'
                        }}
                      >
                        <Play size={16} />
                      </button>
                    ) : (
                      <>
                        <button 
                          onClick={handlePauseStep}
                          title={isVi ? 'Tạm dừng' : 'Pause'}
                          style={{
                            padding: '6px', borderRadius: '8px', border: '1px solid #ddd',
                            backgroundColor: '#fff', color: '#333', cursor: 'pointer',
                            display: 'grid', placeItems: 'center'
                          }}
                        >
                          <Pause size={16} />
                        </button>
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
                      </>
                    )}
                    
                    <button 
                      onClick={handleNextStep} 
                      disabled={activeStepIndex === instructions.length - 1}
                      style={{
                        padding: '6px', borderRadius: '8px', border: 'none',
                        backgroundColor: activeStepIndex === instructions.length - 1 ? '#e9ecef' : '#0f5f59',
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
                        backgroundColor: idx === activeStepIndex ? '#0f5f59' : '#ccc',
                        border: idx === activeStepIndex ? '2px solid #fff' : 'none',
                        boxShadow: idx === activeStepIndex ? '0 0 0 2px #0f5f59' : 'none'
                      }} />
                      
                      <p style={{
                        margin: 0, fontSize: '12px', 
                        fontWeight: idx === activeStepIndex ? '700' : '400',
                        color: idx === activeStepIndex ? '#0f5f59' : '#555'
                      }}>
                        {idx + 1}. {instr}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: '8px', width: '100%' }}>
                <button onClick={handleCancelNavigation} style={{
                  flex: 1, padding: '10px 8px', border: 'none', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '13px',
                  background: 'linear-gradient(135deg, #e0e0e0, #bdbdbd)',
                  color: '#333', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '4px',
                  boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
                }}>
                  <X size={16} />
                  {isVi ? 'Hủy' : 'Cancel'}
                </button>
                <button onClick={handleArrivedOnly} style={{
                  flex: 1.2, padding: '10px 8px', border: '1.5px solid #2e7d32', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '13px',
                  background: '#edf7ed',
                  color: '#2e7d32', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '4px',
                  boxShadow: '0 2px 5px rgba(46,125,50,0.1)'
                }}>
                  <CheckCircle size={16} />
                  {isVi ? 'Đã đến' : 'Arrived'}
                </button>
                <button onClick={handleArrived} style={{
                  flex: 1.8, padding: '10px 8px', border: 'none', borderRadius: '10px',
                  fontWeight: '700', cursor: 'pointer', fontSize: '13px',
                  background: 'linear-gradient(135deg, #4caf50, #388e3c)',
                  color: 'white', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '4px',
                  boxShadow: '0 4px 10px rgba(76,175,80,0.25)'
                }}>
                  <Play size={16} />
                  {isVi ? 'Đến & Giới thiệu' : 'Arrived & Intro'}
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
