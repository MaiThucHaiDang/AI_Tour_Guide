import React from 'react';
import { ArrowLeft, MapPin, Smartphone } from 'lucide-react';
import ExploreDashboard from './dashboard/ExploreDashboard';

const PhonePreview = ({ onBack, language, setLanguage, initialLocation }) => {
  const isVi = language === 'vi';

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

        <h1>{isVi ? 'Đại Nội Huế trong một màn hình điện thoại.' : 'Hue Imperial City in a phone-sized tour.'}</h1>
        <p>
          {isVi
            ? 'Dùng màn hình này khi thuyết trình trên laptop: người xem thấy trực tiếp app mobile với bản đồ, điểm dừng, hỏi AI và điều hướng dưới.'
            : 'Use this view on a laptop presentation: viewers see the mobile app directly with map, stops, AI guide, and bottom navigation.'}
        </p>

        <div className="phone-preview-facts" aria-label={isVi ? 'Thông tin demo' : 'Demo facts'}>
          <span>
            <strong>17</strong>
            {isVi ? 'điểm dừng' : 'stops'}
          </span>
          <span>
            <strong>{isVi ? 'Bản đồ' : 'Map'}</strong>
            {isVi ? 'dẫn đường' : 'routing'}
          </span>
          <span>
            <strong>{isVi ? 'AI' : 'AI'}</strong>
            {isVi ? 'hỏi đáp' : 'guide'}
          </span>
        </div>

        <div className="phone-preview-url">
          <MapPin size={16} />
          <span>localhost:5173/?view=phone</span>
        </div>
      </aside>

      <section className="phone-device-shell" aria-label={isVi ? 'Màn hình điện thoại mô phỏng' : 'Simulated phone screen'}>
        <div className="phone-device" role="presentation">
          <div className="phone-device-side phone-device-side-left" />
          <div className="phone-device-side phone-device-side-right" />
          <div className="phone-device-speaker" />
          <div className="phone-device-screen">
            <ExploreDashboard
              onBack={onBack}
              language={language}
              setLanguage={setLanguage}
              initialLocation={initialLocation}
            />
          </div>
        </div>
      </section>
    </div>
  );
};

export default PhonePreview;
