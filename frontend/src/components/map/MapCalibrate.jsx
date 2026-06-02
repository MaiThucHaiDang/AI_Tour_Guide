import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Save, RefreshCw, ChevronLeft } from 'lucide-react';
import { getMapConfigAPI, saveMapConfigAPI } from '../../services/apiService';

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Helper function to return beautiful custom 2.5D architecture icons
const getCustomIcon = (artifactId) => {
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
  return new L.Icon({
    iconUrl: `/assets/icons/${iconName}`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [46, 46],
    iconAnchor: [23, 45],
    popupAnchor: [0, -40],
    shadowSize: [46, 46]
  });
};

// Hoàng Thành Huế (Đại Nội) Boundary coordinates for Polygon
const IMPERIAL_CITY_BOUNDARY = [
  [16.469447, 107.581697], // Đông Nam
  [16.465889, 107.576669], // Tây Nam
  [16.470200, 107.573342], // Tây Bắc
  [16.473720, 107.578359]  // Đông Bắc
];

// Helper component to update Map view bounds dynamically
const MapBoundsUpdater = ({ bounds }) => {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length === 2 && bounds[0] && bounds[1]) {
      map.fitBounds(bounds, { animate: true });
    }
  }, [bounds, map]);
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

const MapCalibrate = ({ onBack, language = 'vi' }) => {
  const isVi = language === 'vi';
  
  const [mapBounds, setMapBounds] = useState([[16.4625, 107.5706], [16.4765, 107.5854]]);
  const [mapCenter, setMapCenter] = useState(null);
  const [artifactsList, setArtifactsList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [statusType, setStatusType] = useState('success');

  const handleGoToNgoMon = () => {
    setMapCenter([16.467766, 107.579146]);
  };

  // Load coordinates and bounds from DB on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        setIsLoading(true);
        const data = await getMapConfigAPI();
        if (data.success) {
          setMapBounds(data.map_bounds);
          setArtifactsList(data.artifacts);
        }
      } catch (err) {
        console.error('Failed to load map config:', err);
        showStatus(isVi ? 'Không thể tải cấu hình từ database.' : 'Failed to load map config from DB.', 'error');
      } finally {
        setIsLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const showStatus = (msg, type = 'success') => {
    setStatusMessage(msg);
    setStatusType(type);
    setTimeout(() => {
      setStatusMessage(null);
    }, 4000);
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

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const res = await saveMapConfigAPI(mapBounds, artifactsList);
      if (res.success) {
        showStatus(isVi ? 'Đã lưu cấu hình vào Database và file dự phòng thành công!' : 'Saved map configuration to DB and backup file successfully!', 'success');
      }
    } catch (err) {
      console.error('Failed to save config:', err);
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

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f2f5', gap: '15px' }}>
        <style>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .spin {
            animation: spin 1s linear infinite;
          }
        `}</style>
        <RefreshCw className="spin" size={40} color="#0f5f59" />
        <p style={{ fontSize: '16px', fontWeight: '600', color: '#333' }}>
          {isVi ? 'Đang nạp cấu hình bản đồ từ Database...' : 'Loading map configuration from Database...'}
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', position: 'relative' }}>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1.2s linear infinite;
        }
      `}</style>

      {/* ─── Back Header ─── */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '60px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(10px)',
        display: 'flex', alignItems: 'center', padding: '0 20px', zIndex: 2000,
        boxShadow: '0 2px 10px rgba(0,0,0,0.05)', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <button onClick={onBack} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', color: '#1a1a1a', gap: '6px',
            fontSize: '14px', fontWeight: '600'
          }}>
            <ChevronLeft size={24} />
            {isVi ? 'Quay lại' : 'Back'}
          </button>
          <div style={{ height: '24px', width: '1px', backgroundColor: '#ddd' }} />
          <h1 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: '#0f5f59' }}>
            {isVi ? 'Căn Chỉnh Bản Đồ Đại Nội Huế (Leaflet & OSM)' : 'Hue Citadel Map Calibration (Leaflet & OSM)'}
          </h1>
        </div>
        
        <button onClick={handleSave} disabled={isSaving} style={{
          padding: '10px 20px', borderRadius: '10px', border: 'none',
          background: 'linear-gradient(135deg, #4caf50, #388e3c)',
          color: '#fff', fontWeight: '700', fontSize: '14px',
          cursor: isSaving ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center',
          gap: '8px', boxShadow: '0 4px 12px rgba(76,175,80,0.2)', transition: 'all 0.2s'
        }}>
          {isSaving ? <RefreshCw className="spin" size={16} /> : <Save size={16} />}
          {isVi ? 'LƯU VÀO DATABASE' : 'SAVE TO DATABASE'}
        </button>
      </div>

      {/* ─── Status Notification Toast ─── */}
      {statusMessage && (
        <div style={{
          position: 'absolute', top: '75px', right: '20px', zIndex: 3000,
          backgroundColor: statusType === 'success' ? '#d4edda' : '#f8d7da',
          color: statusType === 'success' ? '#155724' : '#721c24',
          border: `1px solid ${statusType === 'success' ? '#c3e6cb' : '#f5c6cb'}`,
          padding: '12px 24px', borderRadius: '10px', fontSize: '14px', fontWeight: '600',
          boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
        }}>
          {statusMessage}
        </div>
      )}

      {/* ─── Left Sidebar Settings Panel ─── */}
      <div style={{
        width: '350px', height: 'calc(100vh - 60px)', marginTop: '60px',
        backgroundColor: '#fff', borderRight: '1px solid #e0e0e0', zIndex: 1000,
        padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px',
        boxShadow: '2px 0 15px rgba(0,0,0,0.03)'
      }}>
        <div>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '15px', fontWeight: '700', color: '#333' }}>
            {isVi ? '1. Co giãn Ảnh bản đồ (MAP_BOUNDS)' : '1. Scale Map Image (MAP_BOUNDS)'}
          </h3>
          <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
            {isVi
              ? 'Thay đổi tọa độ góc Tây Nam (SW - dưới trái) và Đông Bắc (NE - trên phải) để dịch chuyển và thay đổi tỷ lệ của sơ đồ phẳng trên lưới GPS.'
              : 'Adjust Southwest (SW) and Northeast (NE) GPS corners to align the flat overlay image.'}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
            <div>
              <label style={{ fontSize: '11px', color: '#888', fontWeight: '600' }}>SW Latitude</label>
              <input type="number" step="0.0000001" value={mapBounds[0][0]} onChange={(e) => handleBoundsChange('sw', 'lat', e.target.value)} style={{ width: '100%', padding: '8px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#888', fontWeight: '600' }}>SW Longitude</label>
              <input type="number" step="0.0000001" value={mapBounds[0][1]} onChange={(e) => handleBoundsChange('sw', 'lng', e.target.value)} style={{ width: '100%', padding: '8px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '11px', color: '#888', fontWeight: '600' }}>NE Latitude</label>
              <input type="number" step="0.0000001" value={mapBounds[1][0]} onChange={(e) => handleBoundsChange('ne', 'lat', e.target.value)} style={{ width: '100%', padding: '8px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#888', fontWeight: '600' }}>NE Longitude</label>
              <input type="number" step="0.0000001" value={mapBounds[1][1]} onChange={(e) => handleBoundsChange('ne', 'lng', e.target.value)} style={{ width: '100%', padding: '8px', fontSize: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
            </div>
          </div>
        </div>

        <div style={{ height: '1px', backgroundColor: '#eee' }} />

        <div>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '15px', fontWeight: '700', color: '#333' }}>
            {isVi ? '2. Di chuyển các địa điểm' : '2. Move Monument Locations'}
          </h3>
          <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
            {isVi
              ? 'Nhấp giữ và kéo các chấm đỏ trên bản đồ tới đúng điểm đặc trưng trên ảnh. Tọa độ thực sẽ tự động cập nhật bên dưới.'
              : 'Click and drag red markers on the map to place them directly over the image features.'}
          </p>
        </div>

        <div style={{ height: '1px', backgroundColor: '#eee' }} />

        <div>
          <h3 style={{ margin: '0 0 6px 0', fontSize: '14px', fontWeight: '700', color: '#555' }}>
            {isVi ? 'Xuất toado.md' : 'Export toado.md'}
          </h3>
          <textarea readOnly value={getExportedToado()} style={{ width: '100%', height: '100px', fontSize: '11px', padding: '8px', borderRadius: '8px', border: '1px solid #ccc', resize: 'vertical', fontFamily: 'monospace', backgroundColor: '#f9f9f9' }} />
        </div>

        <div>
          <h3 style={{ margin: '0 0 6px 0', fontSize: '14px', fontWeight: '700', color: '#555' }}>
            {isVi ? 'Xuất HUE_ARTIFACTS (code)' : 'Export HUE_ARTIFACTS'}
          </h3>
          <textarea readOnly value={getExportedCode()} style={{ width: '100%', height: '120px', fontSize: '11px', padding: '8px', borderRadius: '8px', border: '1px solid #ccc', resize: 'vertical', fontFamily: 'monospace', backgroundColor: '#f9f9f9' }} />
        </div>
      </div>

      {/* ─── Leaflet Map ─── */}
      <div style={{ flex: 1, height: 'calc(100vh - 60px)', marginTop: '60px', position: 'relative' }}>
        {/* Floating button inside map area */}
        <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 1000 }}>
          <button onClick={handleGoToNgoMon} title={isVi ? 'Về Ngọ Môn (Cổng chính)' : 'Go to Ngo Mon Gate'} style={{
            width: '45px', height: '45px', borderRadius: '12px',
            backgroundColor: '#ff9800', color: '#fff',
            border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}>
            <Compass size={22} />
          </button>
        </div>

        <MapContainer 
          bounds={mapBounds} 
          style={{ height: '100%', width: '100%', zIndex: 1 }} 
          zoomControl={true}
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
          <MapBoundsUpdater bounds={mapBounds} />
          {mapCenter && <MapCenterer center={mapCenter} />}

          {/* Draggable Calibration Markers */}
          {artifactsList.map(art => (
            <Marker 
              key={art.id} 
              position={[art.lat, art.lng]} 
              icon={getCustomIcon(art.id)}
              draggable={true}
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
                <div style={{ textAlign: 'center', minWidth: '160px', fontFamily: 'sans-serif' }}>
                  <strong style={{ fontSize: '13px', display: 'block', marginBottom: '4px', color: '#333' }}>
                    {isVi ? art.name_vi : art.name_en}
                  </strong>
                  <span style={{ fontSize: '11px', color: '#666', fontFamily: 'monospace', display: 'block', marginBottom: '4px' }}>
                    {art.lat.toFixed(7)}, {art.lng.toFixed(7)}
                  </span>
                  <div style={{ fontSize: '10px', color: '#4caf50', fontWeight: 'bold' }}>
                    {isVi ? '👆 Kéo thả để căn chỉnh vị trí' : '👆 Drag to calibrate position'}
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default MapCalibrate;
