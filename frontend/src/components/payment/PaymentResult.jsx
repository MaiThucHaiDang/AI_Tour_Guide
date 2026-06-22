import React, { useEffect, useState } from 'react';
import { ArrowLeft, CheckCircle, XCircle, Clock, MapPin } from 'lucide-react';
import ImageGallery from '../shared/ImageGallery';

const useNotifyOpener = (status) => {
  useEffect(() => {
    if (status && status !== 'loading' && window.opener) {
      const url = window.location.href;
      window.opener.location.href = url;
      window.close();
    }
  }, [status]);
};

const API_BASE = '';

const LOCATION_IMAGES = {
  'Ngọ Môn': ['/assets/images/art_17_1.jpg', '/assets/images/art_17_2.jpg'],
  'Điện Long An': ['/assets/images/art_16_1.jpg', '/assets/images/art_16_2.jpg'],
};

const FOOD_ICONS = {
  nuoc_suoi: '\uD83D\uDCA7',
  nuoc_ngot: '\uD83E\uDD64',
  ca_phe: '\u2615',
  tra_da: '\uD83E\uDDCB',
  banh_mi: '\uD83E\uDD5F',
  banh_trang: '\uD83E\uDD5F',
  bong_ngo: '\uD83C\uDF7F',
  kem: '\uD83C\uDF66',
};

const FOOD_NAMES = {
  nuoc_suoi: { vi: 'Nước suối', en: 'Water' },
  nuoc_ngot: { vi: 'Nước ngọt', en: 'Soft drink' },
  ca_phe: { vi: 'Cà phê', en: 'Coffee' },
  tra_da: { vi: 'Trà đá', en: 'Iced tea' },
  banh_mi: { vi: 'Bánh mì', en: 'Bread' },
  banh_trang: { vi: 'Bánh tráng trộn', en: 'Rice paper mix' },
  bong_ngo: { vi: 'Bỏng ngô', en: 'Popcorn' },
  kem: { vi: 'Kem', en: 'Ice cream' },
};

const PaymentResult = ({ language, onBack }) => {
  const isVi = language === 'vi';
  const [status, setStatus] = useState('loading');
  const [payment, setPayment] = useState(null);
  const [error, setError] = useState('');

  useNotifyOpener(status);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const orderCode = params.get('vnp_TxnRef');

    if (!orderCode) {
      setStatus('error');
      setError(isVi ? 'Không tìm thấy mã đơn hàng' : 'Order code not found');
      return;
    }

    const buildReturnQueryString = () => {
      const returnParams = new URLSearchParams(window.location.search);
      returnParams.delete('view');
      returnParams.delete('frame');
      return returnParams.toString();
    };

    const verifyPayment = async () => {
      try {
        const queryString = buildReturnQueryString();
        const res = await fetch(`${API_BASE}/api/v1/payment/return?${queryString}`);
        const data = await res.json();

        if (data.success) {
          setStatus('success');
        } else {
          setStatus('failed');
          setError(data.message || (isVi ? 'Thanh toán thất bại' : 'Payment failed'));
        }

        const infoRes = await fetch(`${API_BASE}/api/v1/payment/info/${orderCode}`);
        if (infoRes.ok) {
          const infoData = await infoRes.json();
          setPayment(infoData.payment);
        }
      } catch {
        setTimeout(async () => {
          try {
            const queryString = buildReturnQueryString();
            const res = await fetch(`${API_BASE}/api/v1/payment/return?${queryString}`);
            const data = await res.json();
            if (data.success) {
              setStatus('success');
            } else {
              setStatus('failed');
              setError(data.message || '');
            }
            const infoRes = await fetch(`${API_BASE}/api/v1/payment/info/${orderCode}`);
            if (infoRes.ok) {
              const infoData = await infoRes.json();
              setPayment(infoData.payment);
            }
          } catch {
            setStatus('error');
            setError(isVi ? 'Không thể kiểm tra trạng thái đơn hàng' : 'Cannot check order status');
          }
        }, 2000);
      }
    };

    verifyPayment();
  }, []);

  const formatPrice = (vnd) =>
    new Intl.NumberFormat('vi-VN').format(vnd) + ' \u20AB';

  const locationName = payment?.location || '';
  const images = LOCATION_IMAGES[locationName] || [];
  const heroImage = images.length > 0 ? images[0] : null;

  return (
    <div className="payment-page">
      <header className="payment-header">
        <button type="button" className="payment-back-btn" onClick={onBack}>
          <ArrowLeft size={19} />
          {isVi ? 'Quay lại' : 'Back'}
        </button>
        <span>{isVi ? 'Kết quả thanh toán' : 'Payment result'}</span>
      </header>

      <div className={`payment-hero ${heroImage ? '' : 'payment-hero-fallback'}`}>
        {heroImage ? (
          <img src={heroImage} alt={locationName || 'Payment result'} className="payment-hero-img" />
        ) : (
          <div className="payment-hero-fallback-bg" />
        )}
        <div className="payment-hero-overlay">
          <h1 className="payment-hero-title">{locationName || (isVi ? 'Kết quả thanh toán' : 'Payment Result')}</h1>
          {status === 'success' && (
            <div className="payment-hero-price">
              <CheckCircle size={14} />
              <span>{isVi ? 'Thanh toán thành công' : 'Payment successful'}</span>
            </div>
          )}
        </div>
      </div>

      <main className="payment-main">
        {images.length > 0 && (
          <div className="payment-gallery">
            <ImageGallery images={images} className="payment-gallery-grid" imgClassName="payment-gallery-img" />
          </div>
        )}

        <div className="payment-result-card">
          {status === 'loading' && (
            <div className="payment-result-body">
              <Clock size={52} className="payment-result-icon pending" />
              <h2>{isVi ? 'Đang xác nhận...' : 'Confirming...'}</h2>
              <p>{isVi ? 'Vui lòng chờ trong giây lát' : 'Please wait a moment'}</p>
            </div>
          )}

          {status === 'success' && payment && (
            <div className="payment-result-body">
              <div className="payment-result-success-icon">
                <CheckCircle size={52} />
              </div>
              <h2 className="payment-result-success-title">
                {isVi ? 'Thanh toán thành công!' : 'Payment successful!'}
              </h2>
              <div className="payment-result-details">
                <div className="payment-result-row">
                  <span>{isVi ? 'Mã đơn hàng' : 'Order code'}</span>
                  <strong className="payment-result-code">{payment.orderCode}</strong>
                </div>
                <div className="payment-result-row">
                  <span><MapPin size={13} style={{ verticalAlign: 'middle', marginRight: 2 }} /> {isVi ? 'Địa điểm' : 'Location'}</span>
                  <strong>{payment.location}</strong>
                </div>
                <div className="payment-result-row">
                  <span>👤 {isVi ? 'Người lớn' : 'Adults'}</span>
                  <strong>{payment.adultCount || payment.adult_count}</strong>
                </div>
                {(payment.childrenPaidCount || payment.children_paid_count) > 0 && (
                  <div className="payment-result-row">
                    <span>🧒 {isVi ? 'Trẻ em 7-12' : 'Children 7-12'}</span>
                    <strong>{payment.childrenPaidCount || payment.children_paid_count}</strong>
                  </div>
                )}
                {(payment.childrenFreeCount || payment.children_free_count) > 0 && (
                  <div className="payment-result-row">
                    <span>👶 {isVi ? 'Trẻ em (miễn phí)' : 'Children (free)'}</span>
                    <strong>{payment.childrenFreeCount || payment.children_free_count}</strong>
                  </div>
                )}
                {payment.items && payment.items.length > 0 && payment.items.some(it => it.quantity > 0) && (
                  <div className="payment-result-row">
                    <span>🍽️ {isVi ? 'Đồ ăn, nước uống' : 'Food & drinks'}</span>
                    <strong>
                      {payment.items
                        .filter(it => it.quantity > 0)
                        .map(it => `${FOOD_ICONS[it.key] || ''} ${FOOD_NAMES[it.key]?.[isVi ? 'vi' : 'en'] || it.key} x${it.quantity}`)
                        .join(', ')}
                    </strong>
                  </div>
                )}
                <div className="payment-result-divider" />
                <div className="payment-result-row total">
                  <span className="payment-result-total-label">{isVi ? 'Tổng tiền' : 'Total amount'}</span>
                  <strong className="payment-result-total-value">{formatPrice(payment.amount)}</strong>
                </div>
              </div>
              <p className="payment-result-msg">
                {isVi
                  ? 'Cảm ơn bạn đã mua vé. Vui lòng xuất trình mã đơn hàng khi đến tham quan.'
                  : 'Thank you for your purchase. Please show the order code when visiting.'}
              </p>
              <button type="button" className="payment-home-btn" onClick={onBack}>
                {isVi ? 'Quay lại' : 'Back'}
              </button>
            </div>
          )}

          {(status === 'failed' || status === 'error') && (
            <div className="payment-result-body">
              <div className="payment-result-fail-icon">
                <XCircle size={52} />
              </div>
              <h2 style={{ color: '#ef4444' }}>
                {isVi ? 'Thanh toán thất bại' : 'Payment failed'}
              </h2>
              <p>{error || (isVi ? 'Giao dịch không thành công, vui lòng thử lại.' : 'Transaction unsuccessful, please try again.')}</p>
              <button type="button" className="payment-home-btn" onClick={onBack}>
                {isVi ? 'Quay lại' : 'Back'}
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default PaymentResult;
