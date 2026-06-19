import React, { useMemo } from 'react';
import {
  Camera,
  Download,
  Map,
  MessageCircle,
  RotateCcw,
  Volume2
} from 'lucide-react';
import { buildTourSummary } from '../../services/tourMemoryService';
import {
  formatAudioTime,
  formatDateTime,
  getName,
  xmlEscape
} from './passportDisplayUtils';

const buildAlbumHtml = (summary, language) => {
  const title = 'Về với kinh thành';
  const photos = [
    ...(summary.coverPhoto ? [summary.coverPhoto] : []),
    ...(summary.checkInPhotos || [])
  ];
  const photoHtml = photos.length
    ? photos.map((photo) => `
      <figure>
        <img src="${photo.imageBase64}" alt="${xmlEscape(getName(photo, language) || title)}" />
      </figure>
    `).join('')
    : '<p>Chưa có ảnh check-in.</p>';

  return `<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${xmlEscape(title)}</title>
  <style>
    body { margin: 0; font-family: "Segoe UI", Arial, Roboto, sans-serif; background: #f5ead6; color: #1e2524; }
    main { max-width: 960px; margin: 0 auto; padding: 28px; }
    h1 { font-family: "Segoe UI", Arial, Roboto, sans-serif; font-size: clamp(34px, 7vw, 72px); margin: 0 0 28px; text-align: center; font-weight: 800; }
    .album { display: flex; flex-direction: column; gap: 24px; }
    figure { margin: 0; background: var(--color-bg-surface); border: 1px solid #dfcfad; border-radius: 10px; overflow: hidden; box-shadow: 0 14px 38px rgba(0,0,0,.12); }
    figure img { width: 100%; display: block; object-fit: contain; background: #111; }
  </style>
</head>
<body>
  <main>
    <h1>${xmlEscape(title)}</h1>
    <section class="album">${photoHtml}</section>
  </main>
</body>
</html>`;
};

const TripJournal = ({ language, catalog, memory, onResetMemory }) => {
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
    exportAlbum: isVi ? 'Tải album' : 'Download album',
    saveAll: isVi ? 'Lưu tất cả ảnh' : 'Save all photos',
    reset: isVi ? 'Làm mới' : 'Reset',
    photos: isVi ? 'Ảnh đã chụp' : 'Captured photos',
    coverPhoto: isVi ? 'Ảnh bìa chuyến đi' : 'Trip cover photo',
    checkinPhotos: isVi ? 'Album check-in' : 'Check-in album',
    questions: isVi ? 'Câu hỏi đã hỏi AI' : 'Questions asked',
    audio: isVi ? 'Audio đã nghe' : 'Audio listened',
    emptyPhotos: isVi ? 'Ảnh từ camera/quét hiện vật sẽ xuất hiện ở đây.' : 'Camera and scan photos will appear here.',
    emptyQuestions: isVi ? 'Các câu hỏi bạn hỏi AI sẽ được lưu vào nhật ký.' : 'Questions you ask the AI will be saved here.',
    emptyAudio: isVi ? 'Thời gian nghe thuyết minh sẽ được cộng dồn.' : 'Narration listening time will be accumulated.'
  };

  const handleExportAlbum = () => {
    const html = buildAlbumHtml(summary, language);
    const blob = new Blob(['\ufeff', html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ai-tour-guide-checkin-album-${Date.now()}.html`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadPhoto = (base64Data, filename) => {
    try {
      const link = document.createElement('a');
      link.href = base64Data;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Failed to download image:", err);
    }
  };

  const handleDownloadAllPhotos = async () => {
    const photosToDownload = [
      ...(summary.coverPhoto ? [{ data: summary.coverPhoto.imageBase64, name: `cover-photo-${summary.coverPhoto.id || 'main'}.png` }] : []),
      ...(summary.checkInPhotos || []).map((photo, idx) => ({
        data: photo.imageBase64,
        name: `checkin-photo-${photo.id || idx}.png`
      }))
    ];

    for (let i = 0; i < photosToDownload.length; i++) {
      const photo = photosToDownload[i];
      handleDownloadPhoto(photo.data, photo.name);
      await new Promise((resolve) => setTimeout(resolve, 250));
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
            <div className="passport-progress-value">
              <strong>{summary.completedCount}</strong>
              <span>/{summary.totalCount}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="passport-actions">
        <button type="button" onClick={handleExportAlbum}>
          <Download size={17} />
          {copy.exportAlbum}
        </button>
        {summary.photos.length > 0 && (
          <button type="button" onClick={handleDownloadAllPhotos} className="passport-action-save-all">
            <Download size={17} />
            {copy.saveAll}
          </button>
        )}
        <button type="button" onClick={onResetMemory} className="passport-action-reset">
          <RotateCcw size={17} />
          {copy.reset}
        </button>
      </section>

      <section className="passport-journal-section">
        <article className="passport-journal-card">
          <div className="passport-card-title">
            <Camera size={18} />
            <strong>{copy.coverPhoto}</strong>
          </div>
          {summary.coverPhoto ? (
            <figure className="passport-cover-photo">
              <div className="passport-photo-wrapper">
                <img src={summary.coverPhoto.imageBase64} alt={copy.coverPhoto} />
                <button 
                  type="button" 
                  className="passport-photo-download-btn"
                  onClick={() => handleDownloadPhoto(summary.coverPhoto.imageBase64, `cover-photo-${summary.coverPhoto.id}.png`)}
                  title={isVi ? 'Tải ảnh này về' : 'Download this photo'}
                >
                  <Download size={16} />
                </button>
              </div>
              <figcaption>{formatDateTime(summary.coverPhoto.createdAt, language)}</figcaption>
            </figure>
          ) : (
            <p className="passport-empty-note">{isVi ? 'Ảnh bìa sẽ được chụp khi kết thúc chuyến đi.' : 'The cover photo is captured when the trip ends.'}</p>
          )}
        </article>

        <article className="passport-journal-card">
          <div className="passport-card-title">
            <Camera size={18} />
            <strong>{copy.checkinPhotos}</strong>
          </div>
          {summary.checkInPhotos.length > 0 ? (
            <div className="passport-photo-grid">
              {summary.checkInPhotos.slice().reverse().map((photo) => (
                <figure key={photo.id}>
                  <div className="passport-photo-wrapper">
                    <img src={photo.imageBase64} alt={getName(photo, language) || copy.photos} />
                    <button 
                      type="button" 
                      className="passport-photo-download-btn"
                      onClick={() => handleDownloadPhoto(photo.imageBase64, `checkin-photo-${photo.id}.png`)}
                      title={isVi ? 'Tải ảnh này về' : 'Download this photo'}
                    >
                      <Download size={14} />
                    </button>
                  </div>
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
    </div>
  );
};

export default TripJournal;
