import React from 'react';
import { Star } from 'lucide-react';

const StarRating = ({ value = 0, onChange, max = 5, size = 18, readonly = false }) => {
  const stars = [];
  for (let i = 1; i <= max; i++) {
    const filled = i <= Math.round(value);
    stars.push(
      <button
        key={i}
        type="button"
        className={`star-btn ${filled ? 'is-filled' : ''} ${readonly ? 'is-readonly' : ''}`}
        onClick={() => { if (!readonly && onChange) onChange(i); }}
        disabled={readonly}
        aria-label={`${i} star${i > 1 ? 's' : ''}`}
      >
        <Star size={size} fill={filled ? 'currentColor' : 'none'} />
      </button>
    );
  }
  return <div className="star-rating">{stars}</div>;
};

export default StarRating;
