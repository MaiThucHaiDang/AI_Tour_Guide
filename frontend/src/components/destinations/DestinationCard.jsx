import React, { useEffect, useState } from 'react';
import { ArrowRight, Clock, MapPin, Star } from 'lucide-react';

const DestinationCard = ({ destination, language, onSelect, eager = false }) => {
  const isVi = language === 'vi';
  const [ratingSummary, setRatingSummary] = useState(null);
  const name = isVi ? destination.nameVi : destination.nameEn;
  const subtitle = isVi ? destination.subtitleVi : destination.subtitleEn;
  const summary = isVi ? destination.summaryVi : destination.summaryEn;
  const tags = isVi ? destination.tagsVi : destination.tagsEn;
  const duration = isVi ? destination.durationVi : destination.durationEn;
  const address = isVi ? destination.addressVi : destination.addressEn;
  const status = isVi ? destination.statusVi : destination.statusEn;
  const alt = isVi ? destination.imageAltVi : destination.imageAltEn;
  const artifactId = destination.artifactId || destination.id;
  const hasRealRating = ratingSummary && ratingSummary.totalRatings > 0;

  useEffect(() => {
    let cancelled = false;
    setRatingSummary(null);

    if (!artifactId) return () => {
      cancelled = true;
    };

    fetch(`/api/v1/ratings/location/${artifactId}/summary`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!cancelled) {
          setRatingSummary(data?.summary || null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRatingSummary(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [artifactId]);

  return (
    <button
      type="button"
      className="destination-card"
      onClick={() => onSelect(destination)}
      aria-label={isVi ? `Xem chi tiết ${name}` : `View details for ${name}`}
    >
      <span className="destination-card-media">
        <img
          src={destination.image}
          alt={alt}
          loading={eager ? 'eager' : 'lazy'}
          decoding="async"
        />
        {status && <span className="destination-card-status">{status}</span>}
      </span>

      <span className="destination-card-body">
        <span className="destination-card-meta">
          <span>
            <MapPin size={14} />
            {address}
          </span>
          <span>
            <Clock size={14} />
            {duration}
          </span>
        </span>

        <span className="destination-card-title-wrap">
          <strong>{name}</strong>
          <small>{subtitle}</small>
        </span>

        <span className="destination-card-summary">{summary}</span>

        <span className="destination-card-tags" aria-label={isVi ? 'Chủ đề địa điểm' : 'Destination topics'}>
          {tags.slice(0, 3).map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </span>

        <span className="destination-card-footer">
          <span
            className="destination-rating"
            aria-label={hasRealRating
              ? (isVi
                ? `Điểm đánh giá trung bình ${ratingSummary.avgOverall} trên 5 từ ${ratingSummary.totalRatings} đánh giá`
                : `Average rating ${ratingSummary.avgOverall} out of 5 from ${ratingSummary.totalRatings} reviews`)
              : (isVi ? 'Chưa có đánh giá thật' : 'No real reviews yet')}
          >
            <Star size={15} />
            {hasRealRating
              ? `${ratingSummary.avgOverall} (${ratingSummary.totalRatings})`
              : (isVi ? 'Chưa có' : 'No reviews')}
          </span>
          <span className="destination-card-cta">
            {isVi ? 'Xem chi tiết' : 'View details'}
            <ArrowRight size={16} />
          </span>
        </span>
      </span>
    </button>
  );
};

export default DestinationCard;
