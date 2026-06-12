import React, { useEffect, useRef, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  Landmark,
  MapPin,
  MessageCircle,
  Mic,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Smartphone
} from 'lucide-react';
import DestinationGrid from './destinations/DestinationGrid';
import { featuredDestinations } from '../data/destinations';

const REAL_IMAGES = {
  hue: 'https://commons.wikimedia.org/wiki/Special:FilePath/Meridian%20Gate%2C%20Hue%20%28I%29.jpg',
  map: '/map.jpg',
  ngoMon: '/assets/icons/ngo_mon.png',
  thaiHoa: '/assets/icons/thai_hoa.png',
  kienTrung: '/assets/icons/kien_trung.png'
};

const HomeScreen = ({
  onSelectFeature,
  onSelectDestination,
  language,
  setLanguage,
  isPhoneFrame = false
}) => {
  const isVi = language === 'vi';
  const [activeScene, setActiveScene] = useState('hue');
  const [visibleIds, setVisibleIds] = useState(() => new Set(['hero']));
  const [isLaunching, setIsLaunching] = useState(false);
  const rootRef = useRef(null);
  const carouselRef = useRef(null);
  const dragStateRef = useRef({ active: false, startX: 0, scrollLeft: 0 });
  const sectionRefs = useRef({});

  const copy = {
    eyebrow: isVi ? 'AI Tour Guide cho Đại Nội Huế' : 'AI Tour Guide for Hue Imperial City',
    title: isVi
      ? 'Một hướng dẫn viên bỏ túi cho 17 điểm tham quan trong Đại Nội.'
      : 'A pocket guide for 17 stops inside Hue Imperial City.',
    desc: isVi
      ? 'Mở bản đồ Đại Nội, chọn một công trình, hỏi AI bằng giọng nói hoặc văn bản, rồi nghe phần thuyết minh ngay trên điện thoại.'
      : 'Open the Citadel map, choose a monument, ask by voice or text, and hear the guide directly on your phone.',
    primary: isVi ? 'Bắt đầu tham quan' : 'Start touring',
    secondary: isVi ? 'Mở khung điện thoại' : 'Open phone frame',
    navPlaces: isVi ? 'Điểm dừng' : 'Stops',
    navFeatures: isVi ? 'Tính năng' : 'Features',
    heroMeta: isVi ? 'Đại Nội Huế - 17 điểm tham quan - bản đồ & hỏi đáp AI' : 'Hue Imperial City - 17 stops - map & AI guide',
    destinationKicker: isVi ? 'Địa điểm nổi bật' : 'Featured destinations',
    destinationTitle: isVi
      ? 'Chọn một điểm dừng trước, rồi để hướng dẫn viên AI đi cùng bạn.'
      : 'Choose a stop first, then let the AI guide travel with you.',
    destinationText: isVi
      ? 'Mỗi card có ảnh, mô tả ngắn, thời lượng gợi ý và hành động rõ ràng. Chạm vào card để xem thông tin chi tiết trước khi mở bản đồ hoặc hỏi AI.'
      : 'Each card includes an image, short description, suggested duration, and clear action. Tap a card to review details before opening the map or asking AI.',
    storyKicker: isVi ? 'Một luồng tham quan rõ ràng' : 'A focused tour flow',
    storyTitle: isVi
      ? 'Từ bản đồ, đến câu hỏi, đến phần thuyết minh: mọi thứ xoay quanh chuyến đi trong Đại Nội.'
      : 'From map, to question, to narration: everything follows the visitor through the Citadel.',
    featureKicker: isVi ? 'Tính năng cho chuyến tham quan thật' : 'Features for a real visit',
    featureTitle: isVi
      ? 'Người dùng chỉ cần chọn điểm dừng hoặc đặt câu hỏi.'
      : 'Visitors only need to choose a stop or ask a question.',
    outcomeKicker: isVi ? 'Phiên bản hiện tại' : 'Current version',
    outcomeTitle: isVi
      ? 'Tập trung vào Đại Nội Huế, bản đồ mobile và trợ lý thuyết minh AI.'
      : 'Focused on Hue Imperial City, mobile mapping, and AI narration.',
    finalTitle: isVi ? 'Mở không gian tham quan Đại Nội.' : 'Open the Hue Imperial City tour.',
    finalText: isVi
      ? 'Bắt đầu bằng bản đồ, chọn vị trí hiện tại, rồi chạm vào một công trình để hỏi đường hoặc nghe giới thiệu.'
      : 'Start with the map, set your position, then tap a monument for directions or narration.',
    contactTitle: isVi ? 'Đang hỗ trợ' : 'Now supported',
    contactText: isVi
      ? 'Phiên bản này tập trung vào Kinh thành Huế / Đại Nội với bản đồ Leaflet, chỉ đường đi bộ, hỏi đáp AI, nhận diện ảnh và đọc thuyết minh.'
      : 'This version focuses on Hue Imperial City with Leaflet mapping, walking directions, AI Q&A, image recognition, and spoken narration.',
    footerNote: isVi
      ? 'Hiện app đang chạy như một hướng dẫn viên mobile-first cho Đại Nội Huế.'
      : 'The app currently runs as a mobile-first guide for Hue Imperial City.',
    launchText: isVi ? 'Đang mở bản đồ Đại Nội' : 'Opening the Citadel map',
    scenes: [
      {
        id: 'map',
        image: REAL_IMAGES.map,
        place: isVi ? 'Bản đồ Đại Nội' : 'Citadel map',
        eyebrow: isVi ? 'Điểm dừng 01' : 'Stop 01',
        title: isVi ? 'Xem 17 công trình trên một bản đồ tham quan.' : 'See 17 monuments on one tour map.',
        text: isVi
          ? 'Marker công trình, vị trí hiện tại và lộ trình đi bộ được gom trong cùng một màn hình mobile.'
          : 'Monument markers, current position, and walking routes stay together in one mobile screen.',
        prompt: isVi ? 'Chỉ đường tới Ngọ Môn' : 'Navigate to Ngo Mon Gate',
        chips: isVi ? ['Bản đồ', '17 điểm', 'Chỉ đường'] : ['Map', '17 stops', 'Directions']
      },
      {
        id: 'ngo-mon',
        image: REAL_IMAGES.ngoMon,
        place: isVi ? 'Ngọ Môn' : 'Ngo Mon Gate',
        eyebrow: isVi ? 'Điểm dừng 02' : 'Stop 02',
        title: isVi ? 'Chạm một điểm dừng, nghe phần giới thiệu.' : 'Tap a stop and hear the introduction.',
        text: isVi
          ? 'Người dùng có thể nghe giới thiệu ngắn, hỏi tiếp bằng văn bản hoặc dùng giọng nói khi đang di chuyển.'
          : 'Visitors can hear a short intro, follow up by text, or use voice while moving.',
        prompt: isVi ? 'Ngọ Môn có vai trò gì trong triều Nguyễn?' : 'What role did Ngo Mon Gate play?',
        chips: isVi ? ['Nghe giới thiệu', 'Hỏi tiếp', 'Giọng nói'] : ['Narration', 'Follow-up', 'Voice']
      },
      {
        id: 'thai-hoa',
        image: REAL_IMAGES.thaiHoa,
        place: isVi ? 'Điện Thái Hòa' : 'Thai Hoa Palace',
        eyebrow: isVi ? 'Điểm dừng 03' : 'Stop 03',
        title: isVi ? 'Chụp hoặc tải ảnh để giữ đúng ngữ cảnh.' : 'Upload or capture a photo to keep context.',
        text: isVi
          ? 'Khi nhận diện được công trình hoặc hiện vật liên quan, phần hỏi đáp chuyển sang đúng điểm đang xem.'
          : 'When a related monument or artifact is recognized, the guide keeps the conversation tied to that stop.',
        prompt: isVi ? 'Điện Thái Hòa được xây dựng năm nào?' : 'When was Thai Hoa Palace built?',
        chips: isVi ? ['Ảnh', 'Ngữ cảnh', 'Tóm tắt'] : ['Photo', 'Context', 'Summary']
      }
    ],
    features: [
      {
        icon: MapPin,
        title: isVi ? 'Bản đồ Đại Nội' : 'Citadel map',
        text: isVi ? '17 marker công trình với vị trí, popup và hành động rõ ràng trên mobile.' : '17 monument markers with clear mobile actions.'
      },
      {
        icon: Landmark,
        title: isVi ? 'Điểm dừng tham quan' : 'Tour stops',
        text: isVi ? 'Ngọ Môn, Điện Thái Hòa, Điện Kiến Trung, Thế Miếu và các công trình chính.' : 'Ngo Mon Gate, Thai Hoa Palace, Kien Trung Palace, The Mieu, and more.'
      },
      {
        icon: Mic,
        title: isVi ? 'Hỏi AI khi đang đi' : 'Ask while walking',
        text: isVi ? 'Đặt câu hỏi bằng văn bản hoặc giọng nói, rồi nghe câu trả lời ngắn gọn.' : 'Ask by text or voice, then hear a concise answer.'
      },
      {
        icon: ScanSearch,
        title: isVi ? 'Chụp ảnh hiện vật' : 'Capture artifacts',
        text: isVi ? 'Upload hoặc camera giúp AI giữ ngữ cảnh đúng với điểm đang xem.' : 'Upload or camera input helps the AI keep the right context.'
      }
    ],
    outcomes: [
      {
        icon: Landmark,
        title: isVi ? 'Cho khách tự tham quan' : 'For self-guided visitors',
        text: isVi ? 'Không cần đọc bản đồ giấy hay tìm bảng thông tin quá lâu.' : 'No need to rely on paper maps or hunt for long information boards.'
      },
      {
        icon: BookOpen,
        title: isVi ? 'Cho học tập lịch sử Huế' : 'For Hue history learning',
        text: isVi ? 'Câu trả lời ưu tiên ngắn, đúng trọng tâm và gắn với từng công trình.' : 'Answers stay short, focused, and tied to each monument.'
      },
      {
        icon: ShieldCheck,
        title: isVi ? 'Cho trình bày mobile' : 'For mobile presentation',
        text: isVi ? 'Có thể trình bày bằng giả lập điện thoại trên localhost với bản đồ, chat và tab điểm dừng.' : 'Can be presented in a phone-sized localhost viewport with map, chat, and stop detail tabs.'
      }
    ]
  };

  const sceneMap = Object.fromEntries(copy.scenes.map((scene) => [scene.id, scene]));
  const currentScene = sceneMap[activeScene] || copy.scenes[0];

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const revealId = entry.target.dataset.reveal;
          const sceneId = entry.target.dataset.scene;

          if (entry.isIntersecting && revealId) {
            setVisibleIds((prev) => {
              const next = new Set(prev);
              next.add(revealId);
              return next;
            });
          }

          if (entry.isIntersecting && sceneId) {
            setActiveScene(sceneId);
          }
        });
      },
      { threshold: 0.34, rootMargin: '-8% 0px -30% 0px' }
    );

    Object.values(sectionRefs.current).forEach((node) => {
      if (node) observer.observe(node);
    });

    return () => observer.disconnect();
  }, []);

  const setSectionRef = (id) => (node) => {
    if (node) {
      sectionRefs.current[id] = node;
    }
  };

  const revealClass = (id, className = '') => (
    `${className} reveal-on-scroll ${visibleIds.has(id) ? 'is-visible' : ''}`.trim()
  );

  const startExperience = () => {
    if (isLaunching) return;
    setIsLaunching(true);
    window.setTimeout(() => {
      onSelectFeature('dashboard', { id: 1, name_vi: "Kinh thành Huế (Đại Nội)" });
    }, 720);
  };

  const openPhonePreview = () => {
    if (isLaunching) return;
    onSelectFeature('phone', { id: 1, name_vi: "Kinh thành Huế (Đại Nội)", initialTab: 'map' });
  };

  const handleDestinationSelect = (destination) => {
    onSelectDestination?.(destination);
  };

  const handlePointerMove = (event) => {
    const root = rootRef.current;
    if (!root) return;
    const x = event.clientX / window.innerWidth;
    const y = event.clientY / window.innerHeight;
    root.style.setProperty('--move-x', `${(x - 0.5) * 22}px`);
    root.style.setProperty('--move-y', `${(y - 0.5) * 18}px`);
  };

  const handleCarouselPointerDown = (event) => {
    const carousel = carouselRef.current;
    if (!carousel) return;
    dragStateRef.current = {
      active: true,
      startX: event.pageX,
      scrollLeft: carousel.scrollLeft
    };
    carousel.setPointerCapture?.(event.pointerId);
  };

  const handleCarouselPointerMove = (event) => {
    const carousel = carouselRef.current;
    const drag = dragStateRef.current;
    if (!carousel || !drag.active) return;
    const distance = event.pageX - drag.startX;
    carousel.scrollLeft = drag.scrollLeft - distance;
  };

  const stopCarouselDrag = () => {
    dragStateRef.current.active = false;
  };

  return (
    <div className="tour-home landing-page" ref={rootRef} onPointerMove={handlePointerMove}>
      {isLaunching && (
        <div className="journey-transition" aria-live="polite">
          <div className="transition-logo-mark"><span>AI</span></div>
          <strong>AITourGuide</strong>
          <p>{copy.launchText}</p>
        </div>
      )}

      <header className="tour-home-header">
        <div className="tour-home-brand">
          <div className="tour-home-mark brand-logo-mark" aria-hidden="true">
            <span>AI</span>
          </div>
          <div>
            <h1>AITourGuide</h1>
            <p>{isVi ? 'Hướng dẫn viên số cho chuyến tham quan' : 'A digital guide for your visit'}</p>
          </div>
        </div>

        <nav className="landing-nav" aria-label="Landing navigation">
          <a href="#places">{copy.navPlaces}</a>
          <a href="#features">{copy.navFeatures}</a>
        </nav>

        <div className="tour-home-lang">
          <button className={language === 'vi' ? 'active' : ''} onClick={() => setLanguage('vi')}>VI</button>
          <button className={language === 'en' ? 'active' : ''} onClick={() => setLanguage('en')}>EN</button>
        </div>
      </header>

      <main className="tour-home-main">
        <section
          className="landing-hero"
          ref={setSectionRef('hero')}
          data-reveal="hero"
          style={{ '--hero-image': `url(${REAL_IMAGES.hue})` }}
        >
          <div className="hero-shade" />
          <div className={revealClass('hero', 'landing-hero-copy')}>
            <span className="landing-eyebrow">
              <Sparkles size={16} />
              {copy.eyebrow}
            </span>
            <h2>{copy.title}</h2>
            <p>{copy.desc}</p>
            
            <div className="location-picker" style={{ marginTop: '40px' }}>
                <button
                    className="location-card-hero"
                    type="button"
                    onClick={startExperience}
                >
                    <span className="location-card-hero-icon" aria-hidden="true">
                        <Landmark size={36} color="#fff" />
                    </span>
                    <span className="location-card-hero-copy">
                        <strong>{isVi ? 'Đại Nội Huế' : 'Hue Imperial City'}</strong>
                        <small>{isVi ? '17 điểm tham quan - bản đồ - hỏi AI' : '17 tour stops - map - AI guide'}</small>
                        <span>
                            {isVi ? 'Mở bản đồ mobile' : 'Open mobile map'}
                            <ArrowRight size={16} />
                        </span>
                    </span>
                </button>
            </div>

            {!isPhoneFrame && (
              <div className="tour-home-actions phone-preview-actions">
                <button className="secondary-link phone-preview-trigger" onClick={openPhonePreview}>
                  <Smartphone size={18} />
                  <span>{copy.secondary}</span>
                </button>
              </div>
            )}
            
            <div className="hero-route" aria-label={copy.heroMeta} style={{ marginTop: '30px' }}>
              <MapPin size={16} />
              <span>{copy.heroMeta}</span>
            </div>
          </div>
        </section>

        <DestinationGrid
          destinations={featuredDestinations}
          language={language}
          onSelectDestination={handleDestinationSelect}
          kicker={copy.destinationKicker}
          title={copy.destinationTitle}
          description={copy.destinationText}
        />

        <section className="landing-story-shell" id="tour-flow">
          <div className="story-stage-wrap">
            <div className="story-stage">
              {copy.scenes.map((scene) => (
                <div
                  className={`story-image-layer ${activeScene === scene.id ? 'active' : ''}`}
                  style={{ backgroundImage: `linear-gradient(180deg, rgba(9, 17, 18, 0.08), rgba(9, 17, 18, 0.58)), url(${scene.image})` }}
                  key={scene.id}
                />
              ))}
              <div className="story-stage-badge">
                <span>{currentScene.place}</span>
                <strong>{currentScene.eyebrow}</strong>
              </div>
              <div className="story-stage-prompt">
                <MessageCircle size={18} />
                <span>{currentScene.prompt}</span>
              </div>
            </div>
          </div>

          <div className="story-copy">
            <div className="story-heading">
              <span className="section-label">{copy.storyKicker}</span>
              <h2>{copy.storyTitle}</h2>
            </div>

            <div
              className="place-carousel"
              ref={carouselRef}
              onPointerDown={handleCarouselPointerDown}
              onPointerMove={handleCarouselPointerMove}
              onPointerUp={stopCarouselDrag}
              onPointerLeave={stopCarouselDrag}
              aria-label={isVi ? 'Kéo để xem ảnh địa danh' : 'Drag to browse landmark images'}
            >
              {copy.scenes.map((scene) => (
                <button
                  className={`place-slide ${activeScene === scene.id ? 'active' : ''}`}
                  key={scene.id}
                  onClick={() => setActiveScene(scene.id)}
                >
                  <img src={scene.image} alt={scene.place} draggable="false" />
                  <span>{scene.place}</span>
                </button>
              ))}
            </div>

            {copy.scenes.map((scene) => (
              <article
                key={scene.id}
                ref={setSectionRef(scene.id)}
                data-reveal={scene.id}
                data-scene={scene.id}
                className={revealClass(scene.id, `story-card ${activeScene === scene.id ? 'active' : ''}`)}
              >
                <span>{scene.eyebrow}</span>
                <h3>{scene.title}</h3>
                <p>{scene.text}</p>
                <div className="scene-chip-row">
                  {scene.chips.map((chip) => (
                    <strong key={chip}>{chip}</strong>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="feature-pop-section" id="features">
          <div className={revealClass('features-title', 'landing-section-heading')} ref={setSectionRef('features-title')} data-reveal="features-title">
            <span className="section-label">{copy.featureKicker}</span>
            <h2>{copy.featureTitle}</h2>
          </div>

          <div className="feature-pop-grid">
            {copy.features.map(({ icon: Icon, title, text }, index) => {
              const revealId = `feature-${index}`;
              return (
                <article
                  ref={setSectionRef(revealId)}
                  data-reveal={revealId}
                  className={revealClass(revealId, 'feature-pop-card')}
                  style={{ '--delay': `${index * 80}ms` }}
                  key={title}
                >
                  <Icon size={26} />
                  <strong>{title}</strong>
                  <span>{text}</span>
                </article>
              );
            })}
          </div>
        </section>

        <section className="landing-outcomes">
          <div className={revealClass('outcomes-title', 'outcome-heading')} ref={setSectionRef('outcomes-title')} data-reveal="outcomes-title">
            <span className="section-label">{copy.outcomeKicker}</span>
            <h2>{copy.outcomeTitle}</h2>
          </div>
          <div className="outcome-grid">
            {copy.outcomes.map(({ icon: Icon, title, text }, index) => {
              const revealId = `outcome-${index}`;
              return (
                <article
                  ref={setSectionRef(revealId)}
                  data-reveal={revealId}
                  className={revealClass(revealId, 'outcome-card')}
                  style={{ '--delay': `${index * 90}ms` }}
                  key={title}
                >
                  <Icon size={24} />
                  <strong>{title}</strong>
                  <span>{text}</span>
                </article>
              );
            })}
          </div>
        </section>

        <section className={revealClass('final-cta', 'landing-final-cta')} ref={setSectionRef('final-cta')} data-reveal="final-cta">
          <div>
            <span className="section-label">{isVi ? 'Không gian tham quan' : 'Tour workspace'}</span>
            <h2>{copy.finalTitle}</h2>
            <p>{copy.finalText}</p>
          </div>
          <div className="landing-final-actions">
            <button className="primary" onClick={startExperience}>
              <span>{copy.primary}</span>
              <ArrowRight size={18} />
            </button>
            {!isPhoneFrame && (
              <button className="secondary-link phone-preview-trigger" onClick={openPhonePreview}>
                <Smartphone size={18} />
                <span>{copy.secondary}</span>
              </button>
            )}
          </div>
        </section>

        <footer className="landing-footer">
          <div className="footer-brand">
            <div className="brand-logo-mark"><span>AI</span></div>
            <div>
              <strong>AITourGuide</strong>
              <p>{copy.footerNote}</p>
            </div>
          </div>
          <div className="footer-contact">
            <strong>{copy.contactTitle}</strong>
            <p>{copy.contactText}</p>
            <span>{isVi ? 'Dữ liệu: 17 công trình Đại Nội Huế' : 'Data: 17 Hue Imperial City stops'}</span>
            <span>{isVi ? 'Luồng chính: bản đồ, hỏi AI, ảnh, giọng nói' : 'Main flow: map, AI chat, image, voice'}</span>
          </div>
          <div className="footer-sources">
            <strong>{isVi ? 'Nguồn ảnh' : 'Image sources'}</strong>
            <a href="https://commons.wikimedia.org/wiki/File:Meridian_Gate,_Hue_(I).jpg" target="_blank" rel="noreferrer">Hue Imperial City / Wikimedia Commons</a>
            <span>{isVi ? 'Bản đồ và icon công trình: assets local của project' : 'Map and monument icons: local project assets'}</span>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default HomeScreen;
