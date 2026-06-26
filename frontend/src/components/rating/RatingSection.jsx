import React, { useEffect, useState } from 'react';
import { MessageSquare, Star, ChevronDown, X, Clock } from 'lucide-react';
import StarRating from './StarRating';

const API_BASE = '';

const timeAgo = (dateStr, locale = 'vi') => {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (locale === 'en') {
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }
  if (diff < 60) return 'vài giây trước';
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
  return `${Math.floor(diff / 86400)} ngày trước`;
};

const getInitials = (name) => {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

const RatingSection = ({ locationId, locationName, language }) => {
  const isVi = language === 'vi';
  const [summary, setSummary] = useState(null);
  const [ratings, setRatings] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [serviceRating, setServiceRating] = useState(5);
  const [sceneryRating, setSceneryRating] = useState(5);
  const [priceRating, setPriceRating] = useState(5);
  const [review, setReview] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, listRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/ratings/location/${locationId}/summary`),
        fetch(`${API_BASE}/api/v1/ratings/location/${locationId}?perPage=5`),
      ]);
      if (summaryRes.ok) {
        const s = await summaryRes.json();
        setSummary(s.summary);
      }
      if (listRes.ok) {
        const l = await listRes.json();
        setRatings(l.ratings || []);
        setTotal(l.total || 0);
      }
    } catch (e) {
      if (e?.message) setError(e.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (locationId) fetchData();
  }, [locationId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!customerName.trim()) {
      setError(isVi ? 'Vui lòng nhập tên của bạn' : 'Please enter your name');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/ratings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          locationId,
          serviceRating,
          sceneryRating,
          priceRating,
          review: review.trim() || null,
          customerName: customerName.trim(),
        }),
      });
      if (!res.ok) {
        let msg = (isVi ? 'Gửi đánh giá thất bại' : 'Failed to submit review');
        try {
          const err = await res.json();
          if (err.detail) msg = err.detail;
          else if (err.message) msg = err.message;
        } catch (parseError) {
          console.warn('Failed to parse rating error response:', parseError);
        }
        throw new Error(msg);
      }
      setSubmitted(true);
      setReview('');
      setCustomerName('');
      setShowForm(false);
      fetchData();
      setTimeout(() => setSubmitted(false), 3000);
    } catch (e) {
      setError(e.message || (isVi ? 'Gửi đánh giá thất bại' : 'Failed to submit review'));
    }
    setSubmitting(false);
  };

  return (
    <section className="rating-section">
      <h2 className="rating-heading">
        <Star size={18} /> {isVi ? 'Đánh giá & Nhận xét' : 'Ratings & Reviews'}
      </h2>

      {loading ? (
        <div className="rating-loading">{isVi ? 'Đang tải...' : 'Loading...'}</div>
      ) : (
        <>
          {summary && (
            <div className="rating-summary">
              <div className="rating-summary-header">
                <div className="rating-summary-big">
                  <span className="rating-summary-score">{summary.avgOverall}</span>
                  <StarRating value={Math.round(summary.avgOverall)} readonly size={16} />
                </div>
                <div className="rating-summary-count">
                  {isVi
                    ? `${summary.totalRatings} đánh giá`
                    : `${summary.totalRatings} reviews`}
                </div>
              </div>
              <div className="rating-summary-bars">
                <div className="rating-summary-bar">
                  <span className="rating-bar-label">{isVi ? 'Dịch vụ' : 'Service'}</span>
                  <div className="rating-bar-track">
                    <div className="rating-bar-fill" style={{ width: `${(summary.avgService / 5) * 100}%` }} />
                  </div>
                  <span className="rating-bar-value">{summary.avgService}</span>
                </div>
                <div className="rating-summary-bar">
                  <span className="rating-bar-label">{isVi ? 'Cảnh quan' : 'Scenery'}</span>
                  <div className="rating-bar-track">
                    <div className="rating-bar-fill" style={{ width: `${(summary.avgScenery / 5) * 100}%` }} />
                  </div>
                  <span className="rating-bar-value">{summary.avgScenery}</span>
                </div>
                <div className="rating-summary-bar">
                  <span className="rating-bar-label">{isVi ? 'Giá vé' : 'Price'}</span>
                  <div className="rating-bar-track">
                    <div className="rating-bar-fill" style={{ width: `${(summary.avgPrice / 5) * 100}%` }} />
                  </div>
                  <span className="rating-bar-value">{summary.avgPrice}</span>
                </div>
              </div>
            </div>
          )}

          {submitted && (
            <div className="rating-toast">
              {isVi ? 'Cảm ơn bạn đã đánh giá!' : 'Thank you for your review!'}
            </div>
          )}

          <div className="rating-form-wrap">
            {!showForm ? (
              <button type="button" className="rating-write-btn" onClick={() => setShowForm(true)}>
                <MessageSquare size={16} />
                {isVi ? 'Viết đánh giá' : 'Write a review'}
                <ChevronDown size={16} />
              </button>
            ) : (
              <form className="rating-form" onSubmit={handleSubmit}>
                <div className="rating-form-header">
                  <span>{isVi ? 'Đánh giá của bạn' : 'Your review'}</span>
                  <button type="button" className="rating-form-close" onClick={() => setShowForm(false)}>
                    <X size={16} />
                  </button>
                </div>

                <div className="rating-form-row">
                  <span>{isVi ? 'Dịch vụ' : 'Service'}</span>
                  <StarRating value={serviceRating} onChange={setServiceRating} size={22} />
                </div>
                <div className="rating-form-row">
                  <span>{isVi ? 'Cảnh quan' : 'Scenery'}</span>
                  <StarRating value={sceneryRating} onChange={setSceneryRating} size={22} />
                </div>
                <div className="rating-form-row">
                  <span>{isVi ? 'Giá vé' : 'Price'}</span>
                  <StarRating value={priceRating} onChange={setPriceRating} size={22} />
                </div>

                <textarea
                  className="rating-textarea"
                  value={review}
                  onChange={(e) => setReview(e.target.value)}
                  placeholder={isVi ? 'Chia sẻ trải nghiệm của bạn...' : 'Share your experience...'}
                  rows={3}
                />

                <div className="rating-form-name">
                  <input
                    type="text"
                    className="rating-input"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder={isVi ? 'Tên của bạn' : 'Your name'}
                    required
                  />
                </div>

                {error && <div className="rating-error">{error}</div>}

                <button type="submit" className="rating-submit" disabled={submitting}>
                  {submitting
                    ? (isVi ? 'Đang gửi...' : 'Submitting...')
                    : (isVi ? 'Gửi đánh giá' : 'Submit review')}
                </button>
              </form>
            )}
          </div>

          <div className="rating-list">
            {ratings.length === 0 ? (
              <p className="rating-empty">
                {isVi ? 'Chưa có đánh giá nào.' : 'No reviews yet.'}
              </p>
            ) : (
              ratings.map((r) => (
                <div key={r.id} className="rating-item">
                  <div className="rating-item-header">
                    <div className="rating-item-avatar">{getInitials(r.customerName)}</div>
                    <span className="rating-item-name">{r.customerName}</span>
                    <span className="rating-item-time">
                      <Clock size={11} />
                      {timeAgo(r.createdAt, language)}
                    </span>
                  </div>
                  {(r.sceneryRating || r.priceRating) && (
                    <div className="rating-item-dims">
                      {r.sceneryRating && (
                        <span>{isVi ? 'Cảnh quan' : 'Scenery'}: <strong>{r.sceneryRating}/5</strong></span>
                      )}
                      {r.priceRating && (
                        <span>{isVi ? 'Giá vé' : 'Price'}: <strong>{r.priceRating}/5</strong></span>
                      )}
                    </div>
                  )}
                  {r.review && <p className="rating-item-text">{r.review}</p>}
                </div>
              ))
            )}
            {total > ratings.length && (
              <button type="button" className="rating-more-btn" onClick={() => {
                fetch(`${API_BASE}/api/v1/ratings/location/${locationId}?perPage=${total}`)
                  .then(r => r.json())
                  .then(d => { if (d.ratings) setRatings(d.ratings); });
              }}>
                {isVi ? `Xem thêm ${total - ratings.length} đánh giá` : `View ${total - ratings.length} more reviews`}
              </button>
            )}
          </div>
        </>
      )}
    </section>
  );
};

export default RatingSection;
