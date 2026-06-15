import React, { useMemo, useState } from 'react';
import {
  Camera,
  Download,
  Map,
  MessageCircle,
  RotateCcw,
  Share2,
  Volume2
} from 'lucide-react';
import { buildTourSummary } from '../../services/tourMemoryService';
import {
  buildRoutePoints,
  formatAudioTime,
  formatDateTime,
  getName,
  xmlEscape
} from './passportDisplayUtils';

const RouteMiniMap = ({ routeStops, language }) => {
  const points = buildRoutePoints(routeStops);
  const path = points.map((point) => `${point.x},${point.y}`).join(' ');

  return (
    <div className="passport-route-map" aria-label={language === 'vi' ? 'Bản đồ hành trình' : 'Journey map'}>
      {points.length > 0 ? (
        <svg viewBox="0 0 320 180" role="img">
          <rect x="1" y="1" width="318" height="178" rx="8" />
          {points.length > 1 && <polyline points={path} />}
          {points.map((point, index) => (
            <g key={`${point.x}-${point.y}-${index}`}>
              <circle cx={point.x} cy={point.y} r={index === points.length - 1 ? 8 : 6} />
              <text x={point.x} y={point.y + 4}>{index + 1}</text>
            </g>
          ))}
        </svg>
      ) : (
        <div className="passport-empty-map">
          <Map size={30} />
          <span>{language === 'vi' ? 'Hành trình sẽ hiện sau khi bạn check-in.' : 'Your route appears after check-ins.'}</span>
        </div>
      )}
    </div>
  );
};

const buildPosterSvg = (summary, language) => {
  const isVi = language === 'vi';
  const width = 1080;
  const height = 1350;
  const checkedNames = summary.checkedStops
    .slice(0, 8)
    .map((stop, index) => `${index + 1}. ${xmlEscape(stop.displayName)}`)
    .join('\n');
  const title = isVi ? 'Kỷ niệm chuyến đi Đại Nội' : 'Hue Imperial City Memory';
  const progress = `${summary.completedCount}/${summary.totalCount}`;
  const audio = formatAudioTime(summary.totalAudioSeconds, language);
  const questions = summary.questions.length;
  const photos = summary.photos.length;
  const firstPhoto = summary.photos[summary.photos.length - 1]?.imageBase64;
  const routePoints = buildRoutePoints(summary.routeStops, 860, 260, 36);
  const routePath = routePoints.map((point) => `${point.x + 110},${point.y + 865}`).join(' ');
  const stopLines = checkedNames || (isVi ? 'Chưa có điểm check-in' : 'No check-ins yet');

  const photoBlock = firstPhoto
    ? `<image href="${firstPhoto}" x="670" y="290" width="310" height="300" preserveAspectRatio="xMidYMid slice" clip-path="url(#photoClip)" />`
    : `<rect x="670" y="290" width="310" height="300" rx="18" fill="#efe5cf" stroke="#d4c2a1" /><text x="825" y="442" text-anchor="middle" fill="#7d6a4b" font-size="30" font-family="Georgia, serif">${xmlEscape(isVi ? 'Ảnh chuyến đi' : 'Trip photo')}</text>`;

  const routeBlock = routePoints.length > 0
    ? `<polyline points="${routePath}" fill="none" stroke="#075e55" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" />${routePoints.map((point, index) => `<circle cx="${point.x + 110}" cy="${point.y + 865}" r="${index === routePoints.length - 1 ? 17 : 13}" fill="#a83f2e" stroke="#fffaf0" stroke-width="6" />`).join('')}`
    : `<text x="540" y="1005" text-anchor="middle" fill="#6b6252" font-size="34" font-family="Georgia, serif">${xmlEscape(isVi ? 'Bản đồ sẽ hiện sau khi check-in' : 'Route appears after check-ins')}</text>`;

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <clipPath id="photoClip"><rect x="670" y="290" width="310" height="300" rx="18" /></clipPath>
    <style>
      .serif { font-family: Georgia, 'Times New Roman', serif; }
      .sans { font-family: Arial, sans-serif; }
    </style>
  </defs>
  <rect width="${width}" height="${height}" fill="#fff8e8" />
  <rect x="44" y="44" width="992" height="1262" rx="28" fill="#f7f0dc" stroke="#1b2725" stroke-width="3" />
  <rect x="74" y="74" width="932" height="1202" rx="18" fill="none" stroke="#d9c392" stroke-width="2" stroke-dasharray="14 12" />
  <text x="104" y="170" fill="#075e55" font-size="34" font-weight="700" class="sans">AITourGuide Passport</text>
  <text x="104" y="260" fill="#182023" font-size="76" font-weight="700" class="serif">${xmlEscape(title)}</text>
  <text x="104" y="322" fill="#4b5b56" font-size="30" class="sans">${xmlEscape(isVi ? 'Một hành trình tự dẫn trong Hoàng thành Huế' : 'A self-guided walk through Hue Imperial City')}</text>
  <rect x="104" y="392" width="500" height="198" rx="18" fill="#075e55" />
  <text x="140" y="464" fill="#fffaf0" font-size="38" font-weight="700" class="sans">${xmlEscape(isVi ? 'Dấu mộc đã nhận' : 'Stamps collected')}</text>
  <text x="140" y="550" fill="#ffd447" font-size="86" font-weight="700" class="serif">${xmlEscape(progress)}</text>
  ${photoBlock}
  <text x="104" y="704" fill="#182023" font-size="42" font-weight="700" class="serif">${xmlEscape(isVi ? 'Các điểm đã ghé' : 'Visited stops')}</text>
  <text x="104" y="762" fill="#34433f" font-size="28" class="sans" white-space="pre">${stopLines.split('\n').map((line, index) => `<tspan x="104" dy="${index === 0 ? 0 : 42}">${line}</tspan>`).join('')}</text>
  <rect x="104" y="835" width="872" height="330" rx="22" fill="#fffaf0" stroke="#d8c69a" />
  <text x="136" y="910" fill="#075e55" font-size="30" font-weight="700" class="sans">${xmlEscape(isVi ? 'Lộ trình đã đi' : 'Journey route')}</text>
  ${routeBlock}
  <text x="136" y="1235" fill="#182023" font-size="30" font-weight="700" class="sans">${xmlEscape(isVi ? `Ảnh ${photos} · Câu hỏi ${questions} · Audio ${audio}` : `${photos} photos · ${questions} questions · ${audio} audio`)}</text>
</svg>`;
};

const TripJournal = ({ language, catalog, memory, onResetMemory }) => {
  const [exportNotice, setExportNotice] = useState('');
  const summary = useMemo(
    () => buildTourSummary(memory, catalog, language),
    [catalog, language, memory]
  );
  const isVi = language === 'vi';

  const copy = {
    title: isVi ? 'Kỷ niệm chuyến đi Đại Nội' : 'Imperial City Trip Memory',
    subtitle: isVi
      ? 'Tổng kết các điểm đã ghé, ảnh đã chụp, câu hỏi đã hỏi và phần thuyết minh đã nghe.'
      : 'A full summary of visited stops, captured photos, questions, and narration listened to.',
    journey: isVi ? 'Nhật ký sau chuyến đi' : 'Post-trip journal',
    export: isVi ? 'Xuất poster' : 'Export poster',
    reset: isVi ? 'Làm mới' : 'Reset',
    route: isVi ? 'Bản đồ lộ trình' : 'Route map',
    photos: isVi ? 'Ảnh đã chụp' : 'Captured photos',
    questions: isVi ? 'Câu hỏi đã hỏi AI' : 'Questions asked',
    audio: isVi ? 'Audio đã nghe' : 'Audio listened',
    emptyPhotos: isVi ? 'Ảnh từ camera/quét hiện vật sẽ xuất hiện ở đây.' : 'Camera and scan photos will appear here.',
    emptyQuestions: isVi ? 'Các câu hỏi bạn hỏi AI sẽ được lưu vào nhật ký.' : 'Questions you ask the AI will be saved here.',
    emptyAudio: isVi ? 'Thời gian nghe thuyết minh sẽ được cộng dồn.' : 'Narration listening time will be accumulated.',
    exported: isVi ? 'Đã tạo poster chuyến đi.' : 'Trip poster created.'
  };

  const handleExportPoster = async () => {
    const svg = buildPosterSvg(summary, language);
    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const filename = `ai-tour-guide-passport-${Date.now()}.svg`;

    try {
      const file = new File([blob], filename, { type: 'image/svg+xml' });
      if (navigator.canShare?.({ files: [file] }) && navigator.share) {
        await navigator.share({
          title: copy.title,
          text: copy.journey,
          files: [file]
        });
      } else {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
      }
      setExportNotice(copy.exported);
      window.setTimeout(() => setExportNotice(''), 3200);
    } catch (error) {
      console.error('Poster export failed:', error);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="passport-page trip-journal-page">
      <section className="passport-hero">
        <div className="passport-hero-copy">
          <span className="passport-kicker">
            <Map size={16} />
            {copy.journey}
          </span>
          <h2>{copy.title}</h2>
          <p>{copy.subtitle}</p>
        </div>
        <div className="passport-progress-card">
          <div className="passport-progress-ring" style={{ '--progress': `${summary.progressPercent}%` }}>
            <strong>{summary.completedCount}</strong>
            <span>/{summary.totalCount}</span>
          </div>
        </div>
      </section>

      <section className="passport-actions">
        <button type="button" onClick={handleExportPoster}>
          <Share2 size={17} />
          {copy.export}
        </button>
        <button type="button" onClick={onResetMemory}>
          <RotateCcw size={17} />
          {copy.reset}
        </button>
        {exportNotice && <span role="status">{exportNotice}</span>}
      </section>

      <section className="passport-journal-section">
        <article className="passport-journal-card">
          <div className="passport-card-title">
            <Map size={18} />
            <strong>{copy.route}</strong>
          </div>
          <RouteMiniMap routeStops={summary.routeStops} language={language} />
        </article>

        <article className="passport-journal-card">
          <div className="passport-card-title">
            <Camera size={18} />
            <strong>{copy.photos}</strong>
          </div>
          {summary.photos.length > 0 ? (
            <div className="passport-photo-grid">
              {summary.photos.slice().reverse().map((photo) => (
                <figure key={photo.id}>
                  <img src={photo.imageBase64} alt={getName(photo, language) || copy.photos} />
                  <figcaption>{getName(photo, language) || formatDateTime(photo.createdAt, language)}</figcaption>
                </figure>
              ))}
            </div>
          ) : (
            <p className="passport-empty-note">{copy.emptyPhotos}</p>
          )}
        </article>

        <article className="passport-journal-card">
          <div className="passport-card-title">
            <MessageCircle size={18} />
            <strong>{copy.questions}</strong>
          </div>
          {summary.questions.length > 0 ? (
            <ul className="passport-note-list">
              {summary.questions.slice(-8).reverse().map((question) => (
                <li key={question.id}>
                  <span>{getName(question, language) || formatDateTime(question.createdAt, language)}</span>
                  <p>{question.text}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="passport-empty-note">{copy.emptyQuestions}</p>
          )}
        </article>

        <article className="passport-journal-card">
          <div className="passport-card-title">
            <Volume2 size={18} />
            <strong>{copy.audio}</strong>
          </div>
          {summary.audio.length > 0 ? (
            <ul className="passport-note-list">
              {summary.audio.slice(-8).reverse().map((audio) => (
                <li key={audio.id}>
                  <span>{getName(audio, language) || formatDateTime(audio.createdAt, language)}</span>
                  <p>{audio.title || formatAudioTime(audio.seconds, language)}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="passport-empty-note">{copy.emptyAudio}</p>
          )}
        </article>
      </section>

      <button type="button" className="passport-export-fab" onClick={handleExportPoster} aria-label={copy.export}>
        <Download size={18} />
        <span>{copy.export}</span>
      </button>
    </div>
  );
};

export default TripJournal;
