import React, { useEffect, useState, useRef } from 'react';
import { ArrowLeft, CheckCircle, CreditCard, Minus, Plus, ShoppingCart, MapPin } from 'lucide-react';
import ImageGallery from '../shared/ImageGallery';
import MockVnPay from './MockVnPay';

const API_BASE = '';
const ADULT_PRICE = 200000;
const CHILD_PAID_PRICE = 40000;

const FOOD_FALLBACK_ICONS = {
  nuoc_suoi: '\uD83D\uDCA7',
  nuoc_ngot: '\uD83E\uDD64',
  ca_phe: '\u2615',
  tra_da: '\uD83E\uDDCB',
  banh_mi: '\uD83E\uDD5F',
  banh_trang: '\uD83E\uDD5F',
  bong_ngo: '\uD83C\uDF7F',
  kem: '\uD83C\uDF66',
};

const DEST_IMAGES = ['/assets/images/art_17_1.jpg', '/assets/images/art_17_2.jpg'];

const NgocMonCheckout = ({ language, destination, onBack }) => {
  const isVi = language === 'vi';
  const formRef = useRef(null);
  const [adultCount, setAdultCount] = useState(1);
  const [childrenPaidCount, setChildrenPaidCount] = useState(0);
  const [childrenFreeCount, setChildrenFreeCount] = useState(0);
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [foodItems, setFoodItems] = useState([]);
  const [selectedFood, setSelectedFood] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [orderData, setOrderData] = useState(null);
  const [paymentResult, setPaymentResult] = useState(null);

  const ticketTotal = adultCount * ADULT_PRICE + childrenPaidCount * CHILD_PAID_PRICE;
  const foodTotal = foodItems.reduce((sum, item) => sum + (selectedFood[item.key] || 0) * item.price, 0);
  const total = ticketTotal + foodTotal;

  useEffect(() => {
    fetch(API_BASE + '/api/v1/payment/food-items')
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          setFoodItems(Object.entries(data.items).map(([key, val]) => ({ key, ...val })));
        }
      })
      .catch(() => {});
  }, []);

  const fmt = (v) => new Intl.NumberFormat('vi-VN').format(v) + ' \u20AB';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!customerName.trim()) { setError(isVi ? 'Vui lòng nhập họ tên' : 'Please enter your name'); return; }
    if (!customerEmail.trim() || !customerEmail.includes('@')) { setError(isVi ? 'Vui lòng nhập email hợp lệ' : 'Please enter a valid email'); return; }
    if (!customerPhone.trim() || customerPhone.trim().length < 9) { setError(isVi ? 'Vui lòng nhập số điện thoại hợp lệ' : 'Please enter a valid phone number'); return; }

    const itemsPayload = foodItems
      .filter((it) => (selectedFood[it.key] || 0) > 0)
      .map((it) => ({ key: it.key, quantity: selectedFood[it.key] }));

    const isInFrame = window.top !== window;
    let popup = null;
    if (isInFrame) {
      popup = window.open('about:blank', '_blank');
    }

    setLoading(true);

    try {
      const res = await fetch(API_BASE + '/api/v1/payment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: 'Ngọ Môn',
          adultCount,
          childrenPaidCount,
          childrenFreeCount,
          customerName: customerName.trim(),
          customerEmail: customerEmail.trim(),
          customerPhone: customerPhone.trim(),
          items: itemsPayload,
          returnUrl: window.location.origin + '/?view=paymentResult' + (window.top !== window ? '&frame=phone' : ''),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || (isVi ? 'Lỗi tạo đơn hàng' : 'Order creation failed'));
      if (isInFrame) {
        if (popup) {
          popup.location.href = data.paymentUrl;
        } else {
          setOrderData(data);
        }
      } else {
        window.location.href = data.paymentUrl;
      }
    } catch (err) {
      setError(err.message || (isVi ? 'Không thể kết nối đến máy chủ' : 'Cannot connect to server'));
      formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    } finally {
      setLoading(false);
    }
  };

  const handleMockSuccess = () => {
    setPaymentResult('success');
  };

  const handleMockCancel = () => {
    setOrderData(null);
  };

  return (
    <div className="payment-page">
      <header className="payment-header">
        <button type="button" className="payment-back-btn" onClick={onBack}>
          <ArrowLeft size={19} /> {isVi ? 'Quay lại' : 'Back'}
        </button>
        <span>{isVi ? 'Ngọ Môn - Mua vé tham quan' : 'Ngo Mon - Buy tickets'}</span>
      </header>

      <div className="payment-hero">
        <img src={DEST_IMAGES[0]} alt="Ngọ Môn" className="payment-hero-img" />
        <div className="payment-hero-overlay">
          <h1 className="payment-hero-title">Ngọ Môn</h1>
          <p className="payment-hero-sub">
            {isVi ? 'Cổng chính phía Nam của Hoàng thành Huế' : 'The southern ceremonial gate of Hue Imperial City'}
          </p>
          <div className="payment-hero-price">
            <MapPin size={14} />
            <span>{fmt(ADULT_PRICE)} / {isVi ? 'vé người lớn' : 'adult ticket'}</span>
          </div>
        </div>
      </div>

      <main className="payment-main">
        <div className="payment-gallery">
          <ImageGallery images={DEST_IMAGES} className="payment-gallery-grid" imgClassName="payment-gallery-img" />
        </div>

        <div className="payment-card">
          <h2 className="payment-card-title">
            <ShoppingCart size={18} /> {isVi ? 'Thông tin vé' : 'Ticket info'}
          </h2>
          <p className="payment-card-subtitle">
            {isVi
              ? 'Chọn số vé, thêm dịch vụ và điền thông tin để thanh toán nhanh chóng.'
              : 'Choose tickets, add extras and enter your details for a fast checkout.'}
          </p>

          <form ref={formRef} id="checkout-form" onSubmit={handleSubmit} className="payment-form">
            <div className="payment-row">
              <div className="payment-field">
                <label>
                  <span className="payment-label-icon">👤</span>
                  {isVi ? 'Người lớn' : 'Adults'}
                </label>
                <div className="payment-qty-group">
                  <button type="button" className="payment-qty-btn" onClick={() => setAdultCount(Math.max(1, adultCount - 1))}><Minus size={16} /></button>
                  <span className="payment-qty-value">{adultCount}</span>
                  <button type="button" className="payment-qty-btn" onClick={() => setAdultCount(Math.min(100, adultCount + 1))}><Plus size={16} /></button>
                </div>
                <small className="payment-note-text">{fmt(ADULT_PRICE)} / {isVi ? 'vé' : 'ticket'}</small>
              </div>
            </div>

            <div className="payment-row">
              <div className="payment-field">
                <label>
                  <span className="payment-label-icon">🧒</span>
                  {isVi ? 'Trẻ em 7-12 tuổi' : 'Children 7-12'}
                </label>
                <div className="payment-qty-group">
                  <button type="button" className="payment-qty-btn" onClick={() => setChildrenPaidCount(Math.max(0, childrenPaidCount - 1))}><Minus size={16} /></button>
                  <span className="payment-qty-value">{childrenPaidCount}</span>
                  <button type="button" className="payment-qty-btn" onClick={() => setChildrenPaidCount(Math.min(100, childrenPaidCount + 1))}><Plus size={16} /></button>
                </div>
                <small className="payment-note-text">{fmt(CHILD_PAID_PRICE)} / {isVi ? 'vé' : 'ticket'}</small>
              </div>
              <div className="payment-field">
                <label>
                  <span className="payment-label-icon">👶</span>
                  {isVi ? 'Trẻ em dưới 7 tuổi' : 'Children under 7'}
                </label>
                <div className="payment-qty-group">
                  <button type="button" className="payment-qty-btn" onClick={() => setChildrenFreeCount(Math.max(0, childrenFreeCount - 1))}><Minus size={16} /></button>
                  <span className="payment-qty-value">{childrenFreeCount}</span>
                  <button type="button" className="payment-qty-btn" onClick={() => setChildrenFreeCount(Math.min(100, childrenFreeCount + 1))}><Plus size={16} /></button>
                </div>
                <small className="payment-note-text">{isVi ? 'Miễn phí' : 'Free'}</small>
              </div>
            </div>

            <div className="payment-section-divider" />

            <div className="payment-field">
              <label>{isVi ? 'Họ tên' : 'Full name'}</label>
              <input type="text" className="payment-input" value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder={isVi ? 'Nguyễn Văn A' : 'Eg. Nguyen Van A'} required />
            </div>
            <div className="payment-row">
              <div className="payment-field">
                <label>Email</label>
                <input type="email" className="payment-input" value={customerEmail} onChange={(e) => setCustomerEmail(e.target.value)} placeholder="email@example.com" required />
              </div>
              <div className="payment-field">
                <label>{isVi ? 'Số điện thoại' : 'Phone'}</label>
                <input type="tel" className="payment-input" value={customerPhone} onChange={(e) => setCustomerPhone(e.target.value)} placeholder="0901234567" required />
              </div>
            </div>

            {foodItems.length > 0 && (
              <>
                <div className="payment-section-divider" />
                <div className="payment-field">
                  <label className="payment-food-section-label">
                    🍽️ {isVi ? 'Đồ ăn, nước uống' : 'Food & drinks'}
                  </label>
                  <div className="payment-food-list">
                    {foodItems.map((item) => {
                      const isActive = (selectedFood[item.key] || 0) > 0;
                      return (
                        <div key={item.key} className={`payment-food-item${isActive ? ' active' : ''}`}>
                          <div className="payment-food-left">
                            <div className="payment-food-icon">
                              {item.image ? (
                                <img src={item.image} alt={item.name_vi} className="payment-food-img" onError={(e) => { e.target.style.display='none'; e.target.nextSibling.style.display='flex'; }} />
                              ) : null}
                              <span className="payment-food-emoji" style={{ display: item.image ? 'none' : 'flex' }}>
                                {FOOD_FALLBACK_ICONS[item.key] || '🍽️'}
                              </span>
                            </div>
                            <div className="payment-food-info">
                              <span className="payment-food-name">
                                {isVi ? item.name_vi : item.name_en}
                              </span>
                              <span className="payment-food-price">{fmt(item.price)}</span>
                            </div>
                          </div>
                          <div className="payment-qty-group payment-qty-sm">
                            <button type="button" className="payment-qty-btn" onClick={() => setSelectedFood((p) => ({ ...p, [item.key]: Math.max(0, (p[item.key] || 0) - 1) }))}><Minus size={14} /></button>
                            <span className="payment-qty-value payment-qty-sm-value">{selectedFood[item.key] || 0}</span>
                            <button type="button" className="payment-qty-btn" onClick={() => setSelectedFood((p) => ({ ...p, [item.key]: Math.min(50, (p[item.key] || 0) + 1) }))}><Plus size={14} /></button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            )}

            {error && <div className="payment-error">{error}</div>}

            <div className="payment-section-divider" />

            <div className="payment-summary-card">
              <div className="payment-summary-header">
                <span>{isVi ? 'Tóm tắt đơn hàng' : 'Order summary'}</span>
                <strong>{fmt(total)}</strong>
              </div>
              <div className="payment-summary-list">
                <div className="payment-summary-row">
                  <span>{isVi ? 'Vé người lớn' : 'Adult tickets'}</span>
                  <span>{fmt(adultCount * ADULT_PRICE)}</span>
                </div>
                {childrenPaidCount > 0 && (
                  <div className="payment-summary-row">
                    <span>{isVi ? 'Trẻ em 7-12' : 'Children 7-12'}</span>
                    <span>{fmt(childrenPaidCount * CHILD_PAID_PRICE)}</span>
                  </div>
                )}
                {childrenFreeCount > 0 && (
                  <div className="payment-summary-row">
                    <span>{isVi ? 'Trẻ em miễn phí' : 'Free children'}</span>
                    <span>0 ₫</span>
                  </div>
                )}
                {Object.entries(selectedFood).filter(([, q]) => q > 0).length > 0 && (
                  <div className="payment-summary-row">
                    <span>{isVi ? 'Đồ ăn, nước uống' : 'Food & drinks'}</span>
                    <span>{fmt(foodTotal)}</span>
                  </div>
                )}
              </div>
              <div className="payment-total-divider" />
              <div className="payment-total-final">
                <span className="payment-total-label">{isVi ? 'Tổng cộng' : 'Total'}</span>
                <span className="payment-total-value">{fmt(total)}</span>
              </div>
            </div>
          </form>
        </div>

        {paymentResult === 'success' ? (
          <div className="mock-vnpay-overlay">
            <div className="mock-vnpay-card" style={{ textAlign: 'center', padding: '40px 24px' }}>
              <CheckCircle size={56} className="mock-vnpay-success-icon" />
              <h3 style={{ margin: '16px 0 8px', fontSize: '22px' }}>
                {isVi ? 'Đặt vé thành công!' : 'Booking successful!'}
              </h3>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '20px' }}>
                {isVi
                  ? `Mã đơn hàng: ${orderData?.orderCode || ''}`
                  : `Order code: ${orderData?.orderCode || ''}`}
              </p>
              <button className="mock-vnpay-cancel" onClick={onBack} style={{ margin: '0 auto' }}>
                {isVi ? 'Quay lại' : 'Back'}
              </button>
            </div>
          </div>
        ) : (
          <div className="payment-note">
            <p>
              {isVi
                ? 'Bạn sẽ được chuyển đến cổng thanh toán VNPay Sandbox để hoàn tất. Trẻ em dưới 7 tuổi được miễn phí vé.'
                : 'You will be redirected to VNPay Sandbox gateway. Children under 7 are free.'}
            </p>
          </div>
        )}
      </main>

      <div className="payment-bottom-bar">
        <div className="payment-bottom-bar-inner">
          <div className="payment-bottom-total">
            <span className="payment-bottom-total-label">{isVi ? 'Tổng tiền' : 'Total'}</span>
            <span className="payment-bottom-total-value">{fmt(total)}</span>
          </div>
          <button type="submit" form="checkout-form" className="payment-submit" disabled={loading}>
            {loading ? (
              <span className="payment-spinner" />
            ) : (
              <CreditCard size={20} />
            )}
            {loading
              ? (isVi ? 'Đang xử lý...' : 'Processing...')
              : (isVi ? 'Thanh toán qua VNPay' : 'Pay with VNPay')}
          </button>
        </div>
      </div>

      {orderData && !paymentResult && (
        <MockVnPay
          language={language}
          total={total}
          orderCode={orderData.orderCode}
          onSuccess={handleMockSuccess}
          onCancel={handleMockCancel}
        />
      )}
    </div>
  );
};

export default NgocMonCheckout;

