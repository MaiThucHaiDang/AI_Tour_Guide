import React, { useState } from 'react';
import { CheckCircle, CreditCard, Lock } from 'lucide-react';

const MockVnPay = ({ language, total, orderCode, onSuccess, onCancel }) => {
  const isVi = language === 'vi';
  const [step, setStep] = useState('form');
  const fmt = (v) => new Intl.NumberFormat('vi-VN').format(v) + ' ₫';

  const handlePay = () => {
    setStep('processing');
    setTimeout(() => {
      setStep('success');
      setTimeout(() => onSuccess(), 1200);
    }, 1500);
  };

  if (step === 'processing') {
    return (
      <div className="mock-vnpay-overlay">
        <div className="mock-vnpay-card">
          <div className="mock-vnpay-spinner" />
          <h3>{isVi ? 'Đang xử lý thanh toán...' : 'Processing payment...'}</h3>
          <p>{isVi ? 'Vui lòng không tắt trình duyệt' : 'Please do not close the browser'}</p>
        </div>
      </div>
    );
  }

  if (step === 'success') {
    return (
      <div className="mock-vnpay-overlay">
        <div className="mock-vnpay-card">
          <CheckCircle size={48} className="mock-vnpay-success-icon" />
          <h3>{isVi ? 'Thanh toán thành công!' : 'Payment successful!'}</h3>
          <p>{isVi ? 'Đang chuyển đến trang kết quả...' : 'Redirecting to result page...'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mock-vnpay-overlay">
      <div className="mock-vnpay-card">
        <div className="mock-vnpay-header">
          <CreditCard size={20} />
          <span>{isVi ? 'Cổng thanh toán VNPay' : 'VNPay Payment Gateway'}</span>
        </div>

        <div className="mock-vnpay-info">
          <div className="mock-vnpay-row">
            <span>{isVi ? 'Mã đơn hàng:' : 'Order code:'}</span>
            <strong>{orderCode}</strong>
          </div>
          <div className="mock-vnpay-row">
            <span>{isVi ? 'Số tiền:' : 'Amount:'}</span>
            <strong className="mock-vnpay-amount">{fmt(total)}</strong>
          </div>
        </div>

        <div className="mock-vnpay-divider" />

        <div className="mock-vnpay-form">
          <p className="mock-vnpay-form-label">
            {isVi ? 'Thông tin thẻ (mô phỏng)' : 'Card information (simulated)'}
          </p>
          <div className="mock-vnpay-field">
            <label>{isVi ? 'Số thẻ' : 'Card number'}</label>
            <input type="text" className="mock-vnpay-input" value="9704 0000 0000 0018" readOnly />
          </div>
          <div className="mock-vnpay-row-fields">
            <div className="mock-vnpay-field">
              <label>{isVi ? 'Ngày hết hạn' : 'Expiry'}</label>
              <input type="text" className="mock-vnpay-input" value="12/25" readOnly />
            </div>
            <div className="mock-vnpay-field">
              <label>CVV</label>
              <input type="text" className="mock-vnpay-input" value="123" readOnly />
            </div>
          </div>
        </div>

        <div className="mock-vnpay-actions">
          <button className="mock-vnpay-cancel" onClick={onCancel}>
            {isVi ? 'Hủy' : 'Cancel'}
          </button>
          <button className="mock-vnpay-pay" onClick={handlePay}>
            <Lock size={16} />
            {isVi ? 'Thanh toán' : 'Pay'}
          </button>
        </div>

        <p className="mock-vnpay-note">
          <Lock size={12} />
          {isVi
            ? 'Giao diện mô phỏng - không kết nối thật đến VNPay'
            : 'Simulated UI - no actual VNPay connection'}
        </p>
      </div>
    </div>
  );
};

export default MockVnPay;
