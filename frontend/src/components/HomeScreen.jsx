import React from 'react';
import { Camera, Image as ImageIcon, Landmark, MessageCircle, Mic, Sparkles } from 'lucide-react';

const HomeScreen = ({ onSelectFeature, language, setLanguage }) => {
  const isVi = language === 'vi';

  return (
    <div className="tour-home">
      <header className="tour-home-header">
        <div className="tour-home-brand">
          <div className="tour-home-mark"><Landmark size={24} /></div>
          <div>
            <h1>AI Tour Guide</h1>
            <p>{isVi ? 'Hướng dẫn viên số cho chuyến tham quan' : 'A digital guide for your visit'}</p>
          </div>
        </div>
        <div className="tour-home-lang">
          <button className={language === 'vi' ? 'active' : ''} onClick={() => setLanguage('vi')}>VI</button>
          <button className={language === 'en' ? 'active' : ''} onClick={() => setLanguage('en')}>EN</button>
        </div>
      </header>

      <main className="tour-home-main">
        <section className="tour-home-copy">
          <span className="tour-home-eyebrow">
            <Sparkles size={16} />
            {isVi ? 'Khám phá văn hóa' : 'Cultural discovery'}
          </span>
          <h2>
            {isVi
              ? 'Khám phá hiện vật bằng ảnh, giọng nói và hội thoại AI'
              : 'Explore artifacts with images, voice, and AI chat'}
          </h2>
          <p>
            {isVi
              ? 'Chọn địa điểm, chụp hoặc tải ảnh hiện vật, đặt câu hỏi bằng chữ hoặc giọng nói và nhận phần thuyết minh ngắn gọn, dễ hiểu.'
              : 'Choose a destination, capture or upload an artifact, ask by text or voice, and receive concise guidance in context.'}
          </p>
          <div className="tour-home-actions">
            <button className="primary" onClick={() => onSelectFeature('unified')}>
              {isVi ? 'Bắt đầu tham quan' : 'Start exploring'}
            </button>
          </div>
        </section>

        <section className="tour-home-preview" aria-label="AI Tour Guide capabilities">
          <div className="preview-top">
            <span>{isVi ? 'Trải nghiệm chính' : 'Main experience'}</span>
            <strong>{isVi ? 'Sẵn sàng' : 'Ready'}</strong>
          </div>
          <div className="preview-grid">
            <div>
              <Camera size={24} />
              <strong>{isVi ? 'Webcam' : 'Webcam'}</strong>
              <span>{isVi ? 'Chụp ảnh hiện vật' : 'Capture artifacts'}</span>
            </div>
            <div>
              <ImageIcon size={24} />
              <strong>{isVi ? 'Tải ảnh' : 'Upload'}</strong>
              <span>{isVi ? 'Dùng ảnh từ thiết bị' : 'Use photos from your device'}</span>
            </div>
            <div>
              <MessageCircle size={24} />
              <strong>{isVi ? 'Hỏi đáp' : 'Ask'}</strong>
              <span>{isVi ? 'Câu hỏi theo ngữ cảnh' : 'Context-aware Q&A'}</span>
            </div>
            <div>
              <Mic size={24} />
              <strong>{isVi ? 'Giọng nói' : 'Voice'}</strong>
              <span>{isVi ? 'Hỏi bằng lời nói' : 'Ask by speaking'}</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default HomeScreen;
