import React, { useEffect, useState } from 'react';
import { ArrowLeft, CreditCard, Minus, Plus, ShoppingCart } from 'lucide-react';

const API_BASE = '';

const LOCATION_PRICES = {
  'Ngọ Môn': 150000,
  'Điện Long An': 100000,
};

const ALLOWED_LOCATIONS = ['Ngọ Môn', 'Điện Long An'];

const TicketCheckout = ({ language, destination, onBack }) => {
  const isVi = language === 'vi';
  const initialLocation = (destination && (destination.nameVi || destination.name)) || 'Ngọ Môn';
  const [location, setLocation] = useState(initialLocation);
  const [adultCount, setAdultCount] = useState(1);
  const [childrenCount, setChildrenCount] = useState(0);
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [foodItems, setFoodItems] = useState([]);
  const [selectedFood, setSelectedFood] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const unitPrice = LOCATION_PRICES[location] || 0;
  const ticketTotal = adultCount * unitPrice;
  const foodTotal = foodItems.reduce((sum, item) => sum + (selectedFood[item.key] || 0) * item.price, 0);
  const total = ticketTotal + foodTotal;

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/payment/food-items`)
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          const items = Object.entries(data.items).map(([key, val]) => ({ key, ...val }));
          setFoodItems(items);
        }
      })
      .catch(() => {});
  }, []);

  const formatPrice = (vnd) =>
    new Intl.NumberFormat('vi-VN').format(vnd) + ' VND';

  const updateFood = (key, qty) => {
    setSelectedFood((prev) => ({ ...prev, [key]: Math.max(0, Math.min(50, qty)) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!customerName.trim()) {
      setError(isVi ? 'Vui lòng nhập họ tên' : 'Please enter your name');
      return;
    }
    if (!customerEmail.trim() || !customerEmail.includes('@')) {
      setError(isVi ? 'Vui lòng nhập email hợp lệ' : 'Please enter a valid email');
      return;
    }
    if (!customerPhone.trim() || customerPhone.trim().length < 9) {
      setError(isVi ? 'Vui lòng nhập số điện thoại hợp lệ' : 'Please enter a valid phone number');
      return;
    }

    const itemsPayload = foodItems
      .filter((it) => (selectedFood[it.key] || 0) > 0)
      .map((it) => ({ key: it.key, quantity: selectedFood[it.key] }));

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/payment/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location,
          adultCount,
          childrenCount,
          customerName: customerName.trim(),
          customerEmail: customerEmail.trim(),
          customerPhone: customerPhone.trim(),
          items: itemsPayload,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || (isVi ? 'Lỗi tạo đơn hàng' : 'Order creation failed'));
      }
      sessionStorage.setItem('paymentReturnView', JSON.stringify({
        view: 'destination',
        destinationId: destination?.id || null,
      }));
      window.location.href = data.paymentUrl;
    } catch (err) {
      setError(err.message || (isVi ? 'Không thể kết nối đến máy chủ' : 'Cannot connect to server'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="payment-page">
      <header className="payment-header">
        <button type="button" className="payment-back-btn" onClick={onBack}>
          <ArrowLeft size={19} />
          {isVi ? 'Quay lại' : 'Back'}
        </button>
        <span>{isVi ? 'Mua vé tham quan' : 'Buy tickets'}</span>
      </header>

      <main className="payment-main">
        <div className="payment-card">
          <h2 className="payment-card-title">
            <ShoppingCart size={20} />
            {isVi ? 'Thông tin mua vé' : 'Ticket info'}
          </h2>

          <form onSubmit={handleSubmit} className="payment-form">
            <div className="payment-field">
              <label>{isVi ? 'Ðịa đi?m' : 'Location'}</label>
              <div className="payment-location-group">
                {ALLOWED_LOCATIONS.map((loc) => (
                  <button
                    key={loc}
                    type="button"
                    className={`payment-location-btn ${location === loc ? 'active' : ''}`}
                    onClick={() => setLocation(loc)}
                  >
                    <strong>{loc}</strong>
                    <span className="payment-location-price">
                      {formatPrice(LOCATION_PRICES[loc])}/{isVi ? 'vé' : 'ticket'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="payment-row">
              <div className="payment-field">
                <label>{isVi ? 'Người lớn' : 'Adults'}</label>
                <div className="payment-qty-group">
                  <button type="button" className="payment-qty-btn" onClick={() => setAdultCount(Math.max(1, adultCount - 1))}>
                    <Minus size={16} />
                  </button>
                  <span className="payment-qty-value">{adultCount}</span>
                  <button type="button" className="payment-qty-btn" onClick={() => setAdultCount(Math.min(100, adultCount + 1))}>
                    <Plus size={16} />
                  </button>
                </div>
              </div>

              <div className="payment-field">
                <label>{isVi ? 'Trẻ em' : 'Children'}</label>
                <div className="payment-qty-group">
                  <button type="button" className="payment-qty-btn" onClick={() => setChildrenCount(Math.max(0, childrenCount - 1))}>
                    <Minus size={16} />
                  </button>
                  <span className="payment-qty-value">{childrenCount}</span>
                  <button type="button" className="payment-qty-btn" onClick={() => setChildrenCount(Math.min(100, childrenCount + 1))}>
                    <Plus size={16} />
                  </button>
                </div>
                <small className="payment-note-text">
                  {isVi ? 'Tr? em d??i 7 tu?i mi?n ph?' : 'Children under 7 are free'}
                </small>
              </div>
            </div>

            <div className="payment-field">
              <label>{isVi ? 'H? tên' : 'Full name'}</label>
              <input
                type="text"
                className="payment-input"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder={isVi ? 'Nguy?n V?n A' : 'Eg. Nguyen Van A'}
                required
              />
            </div>

            <div className="payment-row">
              <div className="payment-field">
                <label>Email</label>
                <input
                  type="email"
                  className="payment-input"
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  placeholder="email@example.com"
                  required
                />
              </div>
              <div className="payment-field">
                <label>{isVi ? 'S? đi?n tho?i' : 'Phone'}</label>
                <input
                  type="tel"
                  className="payment-input"
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value)}
                  placeholder="0901234567"
                  required
                />
              </div>
            </div>

            {foodItems.length > 0 && (
              <div className="payment-field">
                <label>{isVi ? 'Ð? ?n, nu?c u?ng' : 'Food & drinks'}</label>
                <div className="payment-food-list">
                  {foodItems.map((item) => (
                    <div key={item.key} className="payment-food-item">
                      <span className="payment-food-name">
                        {isVi ? item.name_vi : item.name_en}
                        <small className="payment-food-price">{formatPrice(item.price)}</small>
                      </span>
                      <div className="payment-qty-group payment-qty-sm">
                        <button type="button" className="payment-qty-btn" onClick={() => updateFood(item.key, (selectedFood[item.key] || 0) - 1)}>
                          <Minus size={14} />
                        </button>
                        <span className="payment-qty-value payment-qty-sm-value">{selectedFood[item.key] || 0}</span>
                        <button type="button" className="payment-qty-btn" onClick={() => updateFood(item.key, (selectedFood[item.key] || 0) + 1)}>
                          <Plus size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && <div className="payment-error">{error}</div>}

            <div className="payment-total">
              <div className="payment-total-row">
                <span>{isVi ? 'Vé người lớn' : 'Adult tickets'}</span>
                <span>{formatPrice(ticketTotal)}</span>
              </div>
              {childrenCount > 0 && (
                <div className="payment-total-row">
                  <span>{isVi ? 'Vé tr? em (mi?n ph)' : 'Children (free)'}</span>
                  <span>0 VND</span>
                </div>
              )}
              {Object.entries(selectedFood).filter(([, q]) => q > 0).length > 0 && (
                <div className="payment-total-row">
                  <span>{isVi ? 'Ð? ?n, nu?c u?ng' : 'Food & drinks'}</span>
                  <span>{formatPrice(foodTotal)}</span>
                </div>
              )}
              <div className="payment-total-divider" />
              <div className="payment-total-row payment-total-final">
                <strong>{isVi ? 'Tổng cộng' : 'Total'}</strong>
                <strong>{formatPrice(total)}</strong>
              </div>
            </div>

            <button type="submit" className="payment-submit" disabled={loading}>
              {loading ? (
                <span className="payment-spinner" />
              ) : (
                <CreditCard size={18} />
              )}
              {loading
                ? (isVi ? 'Ðang x? lý...' : 'Processing...')
                : (isVi ? 'Thanh toán qua VNPay' : 'Pay with VNPay')}
            </button>
          </form>
        </div>

        <div className="payment-note">
          <p>{isVi
            ? 'B?n s? đu?c chuy?n đ?n c?ng thanh toán VNPay Sandbox đ? hoàn t?t. Ðây là môi tru?ng th? nghi?m, không thu phí th?t. Tr? em du?i 7 tu?i đu?c mi?n phí vé.'
            : 'You will be redirected to VNPay Sandbox gateway to complete payment. This is a test environment, no real charges. Children under 7 are free.'}
          </p>
        </div>
      </main>
    </div>
  );
};

export default TicketCheckout;
