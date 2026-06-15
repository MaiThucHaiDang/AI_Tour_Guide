export const xmlEscape = (value = '') => String(value)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&apos;');

export const formatDateTime = (iso, language) => {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat(language === 'vi' ? 'vi-VN' : 'en-US', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

export const formatAudioTime = (seconds, language) => {
  const value = Math.max(0, Math.round(Number(seconds || 0)));
  const minutes = Math.floor(value / 60);
  const secs = value % 60;
  if (minutes <= 0) {
    return language === 'vi' ? `${secs} giây` : `${secs}s`;
  }
  return language === 'vi' ? `${minutes} phút ${secs} giây` : `${minutes}m ${secs}s`;
};

export const methodLabel = (method, language) => {
  const labels = {
    gps: language === 'vi' ? 'GPS' : 'GPS',
    scan: language === 'vi' ? 'Quét ảnh' : 'Photo scan',
    arrived: language === 'vi' ? 'Đã tới nơi' : 'Arrived',
    route: language === 'vi' ? 'Theo lộ trình' : 'Route',
    manual: language === 'vi' ? 'Thủ công' : 'Manual'
  };
  return labels[method] || method;
};

export const getName = (item, language) => {
  if (!item) return '';
  return language === 'vi'
    ? item.name_vi || item.nameVi || item.artifactNameVi || item.name_en || item.nameEn || item.artifactNameEn || ''
    : item.name_en || item.nameEn || item.artifactNameEn || item.name_vi || item.nameVi || item.artifactNameVi || '';
};

export const buildRoutePoints = (routeStops, width = 320, height = 180, padding = 24) => {
  const points = routeStops
    .map((stop) => ({
      lat: Number(stop.lat),
      lng: Number(stop.lng)
    }))
    .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lng));

  if (points.length === 0) return [];
  if (points.length === 1) {
    return [{ x: width / 2, y: height / 2 }];
  }

  const minLat = Math.min(...points.map((point) => point.lat));
  const maxLat = Math.max(...points.map((point) => point.lat));
  const minLng = Math.min(...points.map((point) => point.lng));
  const maxLng = Math.max(...points.map((point) => point.lng));
  const latRange = maxLat - minLat || 1;
  const lngRange = maxLng - minLng || 1;

  return points.map((point) => ({
    x: padding + ((point.lng - minLng) / lngRange) * (width - padding * 2),
    y: padding + ((maxLat - point.lat) / latRange) * (height - padding * 2)
  }));
};
