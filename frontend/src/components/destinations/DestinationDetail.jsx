import React from 'react';
import {
  ArrowLeft,
  ArrowRight,
  CalendarClock,
  Clock,
  MapPin,
  MessageCircle,
  Route,
  Sparkles,
  Ticket
} from 'lucide-react';

const DestinationDetail = ({
  destination,
  language,
  onBack,
  onStartTour,
  onAskGuide
}) => {
  const isVi = language === 'vi';
  const name = isVi ? destination.nameVi : destination.nameEn;
  const subtitle = isVi ? destination.subtitleVi : destination.subtitleEn;
  const description = isVi ? destination.descriptionVi : destination.descriptionEn;
  const summary = isVi ? destination.summaryVi : destination.summaryEn;
  const address = isVi ? destination.addressVi : destination.addressEn;
  const duration = isVi ? destination.durationVi : destination.durationEn;
  const openHours = isVi ? destination.openHoursVi : destination.openHoursEn;
  const ticket = isVi ? destination.ticketVi : destination.ticketEn;
  const tags = isVi ? destination.tagsVi : destination.tagsEn;
  const highlights = isVi ? destination.highlightsVi : destination.highlightsEn;
  const tips = isVi ? destination.tipsVi : destination.tipsEn;
  const author = isVi ? destination.authorVi : destination.authorEn;
  const alt = isVi ? destination.imageAltVi : destination.imageAltEn;

  return (
    <div className="destination-detail-page">
      <header className="destination-detail-header">
        <button type="button" className="destination-back-button" onClick={onBack}>
          <ArrowLeft size={19} />
          {isVi ? 'Quay lại danh sách' : 'Back to list'}
        </button>
        <span>{isVi ? 'Chi tiết điểm tham quan' : 'Destination detail'}</span>
      </header>

      <main className="destination-detail-main">
        <section className="destination-detail-hero">
          <div className="destination-detail-image">
            <img src={destination.image} alt={alt} decoding="async" />
          </div>

          <div className="destination-detail-copy">
            <span className="landing-eyebrow">
              <Sparkles size={16} />
              {isVi ? 'Điểm nổi bật trong Đại Nội' : 'Featured stop in the Citadel'}
            </span>
            <h1>{name}</h1>
            <p className="destination-detail-subtitle">{subtitle}</p>
            <p>{description}</p>

            <div className="destination-detail-tags" aria-label={isVi ? 'Chủ đề địa điểm' : 'Destination topics'}>
              {tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>

            <div className="destination-detail-actions">
              <button type="button" className="primary" onClick={() => onStartTour(destination)}>
                <Route size={18} />
                <span>{isVi ? 'Bắt đầu tham quan' : 'Start touring'}</span>
                <ArrowRight size={18} />
              </button>
              <button type="button" className="destination-secondary-button" onClick={() => onAskGuide(destination)}>
                <MessageCircle size={18} />
                <span>{isVi ? 'Hỏi AI về điểm này' : 'Ask AI about this stop'}</span>
              </button>
            </div>
          </div>
        </section>

        <section className="destination-fact-strip" aria-label={isVi ? 'Thông tin nhanh' : 'Quick facts'}>
          <div>
            <MapPin size={18} />
            <span>{isVi ? 'Vị trí' : 'Location'}</span>
            <strong>{address}</strong>
          </div>
          <div>
            <Clock size={18} />
            <span>{isVi ? 'Thời lượng' : 'Duration'}</span>
            <strong>{duration}</strong>
          </div>
          <div>
            <CalendarClock size={18} />
            <span>{isVi ? 'Giờ mở cửa' : 'Open hours'}</span>
            <strong>{openHours}</strong>
          </div>
          <div>
            <Ticket size={18} />
            <span>{isVi ? 'Vé' : 'Ticket'}</span>
            <strong>{ticket}</strong>
          </div>
        </section>

        <section className="destination-detail-content">
          <article>
            <span className="section-label">{isVi ? 'Tóm tắt' : 'Summary'}</span>
            <h2>{isVi ? 'Vì sao nên dừng lại ở đây?' : 'Why stop here?'}</h2>
            <p>{summary}</p>
            <dl className="destination-history-meta">
              <div>
                <dt>{isVi ? 'Niên đại' : 'Year'}</dt>
                <dd>{destination.year || (isVi ? 'Đang cập nhật' : 'To be updated')}</dd>
              </div>
              <div>
                <dt>{isVi ? 'Gắn với' : 'Associated with'}</dt>
                <dd>{author || (isVi ? 'Triều Nguyễn' : 'Nguyen Dynasty')}</dd>
              </div>
            </dl>
          </article>

          <article>
            <span className="section-label">{isVi ? 'Gợi ý trải nghiệm' : 'Experience cues'}</span>
            <h2>{isVi ? 'Điểm đáng chú ý' : 'What to notice'}</h2>
            <ul className="destination-check-list">
              {highlights.map((highlight) => (
                <li key={highlight}>{highlight}</li>
              ))}
            </ul>
          </article>

          <article>
            <span className="section-label">{isVi ? 'Lưu ý' : 'Visitor notes'}</span>
            <h2>{isVi ? 'Trước khi đi tiếp' : 'Before you continue'}</h2>
            <ul className="destination-check-list">
              {tips.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          </article>
        </section>
      </main>
    </div>
  );
};

export default DestinationDetail;
