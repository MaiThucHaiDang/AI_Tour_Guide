import React from 'react';
import { ArrowLeft, MapPin, Smartphone } from 'lucide-react';

const PhonePreview = ({ onBack, language }) => {
  const isVi = language === 'vi';
  const phoneAppSrc = '/?frame=phone';

  return (
    <div className="phone-preview-stage phone-preview-mode">
      <aside className="phone-preview-copy" aria-label={isVi ? 'Chế độ trình bày mobile' : 'Mobile presentation mode'}>
        <button className="phone-preview-back" onClick={onBack}>
          <ArrowLeft size={18} />
          <span>{isVi ? 'Về trang chính' : 'Back home'}</span>
        </button>

        <span className="phone-preview-kicker">
          <Smartphone size={16} />
          {isVi ? 'Khung trình bày mobile' : 'Mobile presentation frame'}
        </span>

        <h1>{isVi ? 'Toàn bộ website trong một màn hình điện thoại.' : 'The full website in a phone-sized flow.'}</h1>
        <p>
          {isVi
            ? 'Khung này bắt đầu từ landing page, rồi đi tiếp tới bản đồ, hỏi AI, nhận diện ảnh và chi tiết điểm dừng như một người dùng mobile thật.'
            : 'This frame starts from the landing page, then continues into map, AI guide, image recognition, and stop details like a real mobile user.'}
        </p>

        <div className="phone-preview-facts" aria-label={isVi ? 'Thông tin trải nghiệm mobile' : 'Mobile experience facts'}>
          <span>
            <strong>{isVi ? 'Landing' : 'Landing'}</strong>
            {isVi ? 'mở đầu' : 'entry'}
          </span>
          <span>
            <strong>{isVi ? 'Bản đồ' : 'Map'}</strong>
            {isVi ? '17 điểm' : '17 stops'}
          </span>
          <span>
            <strong>{isVi ? 'AI' : 'AI'}</strong>
            {isVi ? 'ảnh, giọng nói' : 'photo, voice'}
          </span>
        </div>

        <div className="phone-preview-url">
          <MapPin size={16} />
          <span>{isVi ? 'Mở như một người đang đứng trong Đại Nội' : 'Open it like a visitor inside the Imperial City'}</span>
        </div>
      </aside>

      <section className="phone-device-shell" aria-label={isVi ? 'Màn hình điện thoại mô phỏng' : 'Simulated phone screen'}>
        <div className="phone-device" role="presentation">
          <div className="phone-device-side phone-device-side-left" />
          <div className="phone-device-side phone-device-side-right" />
          <div className="phone-device-speaker" />
          <div className="phone-device-screen">
            <iframe
              className="phone-device-app-frame"
              src={phoneAppSrc}
              title={isVi ? 'AITourGuide mobile app' : 'AITourGuide mobile app'}
            />
          </div>
        </div>
      </section>
    </div>
  );
};

export default PhonePreview;
