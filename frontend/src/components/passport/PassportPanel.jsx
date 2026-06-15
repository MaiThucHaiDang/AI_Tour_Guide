import React, { useMemo } from 'react';
import {
  Award,
  BookOpen,
  Camera,
  CheckCircle2,
  Flag,
  MessageCircle,
  RotateCcw,
  Sparkles,
  Volume2
} from 'lucide-react';
import { buildTourSummary } from '../../services/tourMemoryService';
import { formatAudioTime, formatDateTime, methodLabel } from './passportDisplayUtils';

const PassportPanel = ({
  language,
  catalog,
  memory,
  onResetMemory,
  onEndTrip
}) => {
  const summary = useMemo(
    () => buildTourSummary(memory, catalog, language),
    [catalog, language, memory]
  );
  const isVi = language === 'vi';

  const copy = {
    title: isVi ? 'Hộ chiếu tham quan Đại Nội' : 'Imperial City Passport',
    subtitle: isVi
      ? 'Check-in bằng GPS hoặc ảnh quét để nhận dấu mộc cho từng điểm dừng.'
      : 'Check in by GPS or photo scan to collect a stamp for each stop.',
    stamps: isVi ? 'Dấu mộc' : 'Stamps',
    endTrip: isVi ? 'Kết thúc chuyến đi' : 'End trip',
    reset: isVi ? 'Làm mới' : 'Reset',
    checked: isVi ? 'Đã nhận dấu' : 'Stamped',
    pending: isVi ? 'Chưa nhận dấu' : 'Not stamped',
    photos: isVi ? 'Ảnh đã chụp' : 'Captured photos',
    questions: isVi ? 'Câu hỏi đã hỏi AI' : 'Questions asked',
    audio: isVi ? 'Audio đã nghe' : 'Audio listened'
  };

  return (
    <div className="passport-page passport-page-compact">
      <section className="passport-hero">
        <div className="passport-hero-copy">
          <span className="passport-kicker">
            <BookOpen size={16} />
            {copy.stamps}
          </span>
          <h2>{copy.title}</h2>
          <p>{copy.subtitle}</p>
        </div>
        <div className="passport-progress-card">
          <div className="passport-progress-ring" style={{ '--progress': `${summary.progressPercent}%` }}>
            <strong>{summary.completedCount}</strong>
            <span>/{summary.totalCount}</span>
          </div>
          <div>
            <span>{copy.checked}</span>
            <strong>{summary.progressPercent}%</strong>
          </div>
        </div>
      </section>

      <section className="passport-stat-grid">
        <article>
          <Award size={20} />
          <span>{copy.stamps}</span>
          <strong>{summary.completedCount}/{summary.totalCount}</strong>
        </article>
        <article>
          <Camera size={20} />
          <span>{copy.photos}</span>
          <strong>{summary.photos.length}</strong>
        </article>
        <article>
          <MessageCircle size={20} />
          <span>{copy.questions}</span>
          <strong>{summary.questions.length}</strong>
        </article>
        <article>
          <Volume2 size={20} />
          <span>{copy.audio}</span>
          <strong>{formatAudioTime(summary.totalAudioSeconds, language)}</strong>
        </article>
      </section>

      <section className="passport-actions">
        <button type="button" onClick={onEndTrip}>
          <Flag size={17} />
          {copy.endTrip}
        </button>
        <button type="button" onClick={onResetMemory}>
          <RotateCcw size={17} />
          {copy.reset}
        </button>
      </section>

      <section className="passport-stamp-section">
        <div className="passport-section-heading">
          <Sparkles size={17} />
          <h3>{copy.stamps}</h3>
        </div>
        <div className="passport-stamp-grid">
          {summary.stops.map(({ artifact, checkIn, checked, displayName }, index) => (
            <article className={`passport-stamp-card ${checked ? 'is-stamped' : ''}`} key={artifact.id}>
              <div className="passport-stamp-seal">
                {checked ? <CheckCircle2 size={25} /> : <span>{index + 1}</span>}
              </div>
              <div>
                <strong>{displayName}</strong>
                <span>
                  {checked
                    ? formatDateTime(checkIn.firstCheckedAt, language)
                    : copy.pending}
                </span>
              </div>
              {checked && (
                <div className="passport-method-row">
                  {(checkIn.methods || []).map((method) => (
                    <small key={method}>{methodLabel(method, language)}</small>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
};

export default PassportPanel;
