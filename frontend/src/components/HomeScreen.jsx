import React, { useEffect, useRef, useState } from 'react';
import {
  BookOpen,
  Landmark,
  MapPin,
  Mic,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Smartphone,
  Sun,
  Moon
} from 'lucide-react';
import DestinationGrid from './destinations/DestinationGrid';
import { destinations } from '../data/destinations';
import styles from './HomeScreen.module.css';

const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)';

const REAL_IMAGES = {
  hue: '/assets/images/art_17_1.jpg',
  map: '/map.jpg'
};

const HomeScreen = ({
  onSelectFeature,
  onSelectDestination,
  onOpenBlog,
  language,
  setLanguage,
  isPhoneFrame = false
}) => {
  const isVi = language === 'vi';
  const [visibleIds, setVisibleIds] = useState(() => new Set(['hero']));
  const [isLaunching, setIsLaunching] = useState(false);

  // Theme state
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('tour-theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('tour-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const rootRef = useRef(null);
  const pointerFrameRef = useRef(0);
  const pointerPositionRef = useRef({ x: 0.5, y: 0.5 });
  const prefersReducedMotionRef = useRef(false);
  const sectionRefs = useRef({});

  const copy = {
    eyebrow: isVi ? 'AI Tour Guide Đại Nội Huế' : 'AI Tour Guide Hue Imperial City',
    title: isVi
      ? 'Bản đồ di tích & Hướng dẫn viên thuyết minh AI'
      : 'Monument Map & AI Tour Guide',
    desc: isVi
      ? 'Mở bản đồ, chọn điểm dừng di tích, hỏi AI hoặc nghe thuyết minh trực tiếp ngay trên điện thoại.'
      : 'Open the map, select a stop, ask AI or hear audio guide directly on your phone.',
    primary: isVi ? 'Bắt đầu tham quan' : 'Start touring',
    secondary: isVi ? 'Mở khung điện thoại' : 'Open phone frame',
    navPlaces: isVi ? 'Điểm dừng' : 'Stops',
    navFeatures: isVi ? 'Tính năng' : 'Features',
    navBlog: isVi ? 'Cẩm nang' : 'Guide',
    heroMeta: isVi ? 'Đại Nội Huế - 17 điểm tham quan - bản đồ & hỏi đáp AI' : 'Hue Imperial City - 17 stops - map & AI guide',
    destinationKicker: isVi ? 'Địa điểm nổi bật' : 'Featured destinations',
    destinationTitle: isVi
      ? 'Chọn một điểm dừng trước, rồi để hướng dẫn viên AI đi cùng bạn.'
      : 'Choose a stop first, then let the AI guide travel with you.',
    destinationText: isVi
      ? 'Mỗi điểm dừng có ảnh, mô tả ngắn, thời lượng gợi ý và hành động rõ ràng. Chạm vào một địa điểm để xem trước khi mở bản đồ hoặc hỏi AI.'
      : 'Each stop includes an image, short description, suggested duration, and clear action. Tap a place to review it before opening the map or asking AI.',
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
    contactTitle: isVi ? 'Có thể dùng ngay tại Đại Nội' : 'Ready for an Imperial City visit',
    contactText: isVi
      ? 'Mở bản đồ, chọn điểm dừng, hỏi đường, nghe thuyết minh hoặc chụp ảnh công trình để giữ đúng ngữ cảnh tham quan.'
      : 'Open the map, choose a stop, ask for directions, hear narration, or capture a monument to keep the visit in context.',
    footerNote: isVi
      ? 'Hướng dẫn viên bỏ túi cho hành trình trong Đại Nội Huế.'
      : 'A pocket guide for Hue Imperial City.',
    launchText: isVi ? 'Đang mở bản đồ Đại Nội' : 'Opening the Citadel map',

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
        title: isVi ? 'Cho nhóm đi bằng điện thoại' : 'For phone-first visits',
        text: isVi ? 'Bản đồ, hỏi đáp và thông tin điểm dừng được gom vào một luồng dễ dùng khi đang di chuyển.' : 'Map, Q&A, and stop details stay in one flow while visitors are moving.'
      }
    ]
  };



  useEffect(() => {
    const mediaQuery = window.matchMedia(REDUCED_MOTION_QUERY);
    const updateMotionPreference = () => {
      prefersReducedMotionRef.current = mediaQuery.matches;
    };

    updateMotionPreference();

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', updateMotionPreference);
    } else {
      mediaQuery.addListener(updateMotionPreference);
    }

    return () => {
      if (pointerFrameRef.current) {
        window.cancelAnimationFrame(pointerFrameRef.current);
      }
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', updateMotionPreference);
      } else {
        mediaQuery.removeListener(updateMotionPreference);
      }
    };
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const revealId = entry.target.dataset.reveal;

          if (entry.isIntersecting && revealId) {
            setVisibleIds((prev) => {
              if (prev.has(revealId)) return prev;
              const next = new Set(prev);
              next.add(revealId);
              return next;
            });
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

  const startMapExperience = () => {
    if (isLaunching) return;
    setIsLaunching(true);
    window.setTimeout(() => {
      onSelectFeature('dashboard', { id: 1, name_vi: "Kinh thành Huế (Đại Nội)", initialTab: 'map' });
    }, 720);
  };

  const startChatExperience = () => {
    if (isLaunching) return;
    setIsLaunching(true);
    window.setTimeout(() => {
      onSelectFeature('dashboard', { id: 1, name_vi: "Kinh thành Huế (Đại Nội)", initialTab: 'ask' });
    }, 720);
  };

  const openPhonePreview = () => {
    if (isLaunching) return;
    onSelectFeature('phone', { id: 1, name_vi: "Kinh thành Huế (Đại Nội)", initialTab: 'map' });
  };

  const handleDestinationSelect = (destination) => {
    onSelectDestination?.(destination);
  };

  const handleOpenBlog = (event) => {
    event.preventDefault();
    onOpenBlog?.();
  };

  const handlePointerMove = (event) => {
    const root = rootRef.current;
    if (!root || prefersReducedMotionRef.current) return;
    pointerPositionRef.current = {
      x: event.clientX / window.innerWidth,
      y: event.clientY / window.innerHeight
    };

    if (pointerFrameRef.current) return;

    pointerFrameRef.current = window.requestAnimationFrame(() => {
      const { x, y } = pointerPositionRef.current;
      root.style.setProperty('--move-x', `${(x - 0.5) * 22}px`);
      root.style.setProperty('--move-y', `${(y - 0.5) * 18}px`);
      pointerFrameRef.current = 0;
    });
  };



  return (
    <div className={styles.tourHome} ref={rootRef} onPointerMove={handlePointerMove}>
      <div className={styles.backgroundGlow} />
      <div className={styles.backgroundGlowAccent} />

      {isLaunching && (
        <div className={styles.journeyTransition} aria-live="polite">
          <div className={styles.transitionLogoMark}><span>AI</span></div>
          <strong>AITourGuide</strong>
          <p>{copy.launchText}</p>
        </div>
      )}

      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.logoMark} aria-hidden="true">
            <span>AI</span>
          </div>
          <div className={styles.brandText}>
            <h1>AITourGuide</h1>
            <p>{isVi ? 'Hướng dẫn viên số' : 'A digital guide'}</p>
          </div>
        </div>

        <nav className={styles.nav} aria-label="Landing navigation">
          <a href="#places">{copy.navPlaces}</a>
          <a href="#features">{copy.navFeatures}</a>
          <a href="/blog" onClick={handleOpenBlog}>{copy.navBlog}</a>
        </nav>

        <div className={styles.langToggle} style={{ display: 'flex', gap: '12px' }}>
          <div>
            <button className={language === 'vi' ? styles.active : ''} onClick={() => setLanguage('vi')}>VI</button>
            <button className={language === 'en' ? styles.active : ''} onClick={() => setLanguage('en')}>EN</button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', background: 'var(--color-bg-surface-glass)', borderRadius: 'var(--radius-full)', padding: '2px' }}>
            <button onClick={toggleTheme} style={{ padding: '6px 12px', border: 'none', background: 'transparent', color: 'var(--color-text-main)', cursor: 'pointer', display: 'flex', alignItems: 'center' }} aria-label="Toggle Theme">
              {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
            </button>
          </div>
        </div>
      </header>

      <main className={styles.main}>
        <section
          className={styles.hero}
          ref={setSectionRef('hero')}
          data-reveal="hero"
        >
          <div className={styles.heroBackground} style={{ backgroundImage: `url(${REAL_IMAGES.hue})` }} />
          <div className={styles.heroContent}>
            <span className={styles.eyebrow}>
              <Sparkles size={16} />
              {copy.eyebrow}
            </span>
            <h2 className={styles.heroTitle}>{copy.title}</h2>
            <p className={styles.heroDesc}>{copy.desc}</p>
            
            <div className={styles.ctas}>
                <button
                    className={styles.btnPrimary}
                    type="button"
                    onClick={startMapExperience}
                >
                    <Landmark size={20} />
                    <span>{isVi ? 'Mở bản đồ Đại Nội' : 'Open Citadel Map'}</span>
                </button>
                <button
                    className={styles.btnSecondary}
                    type="button"
                    onClick={startChatExperience}
                >
                    <Sparkles size={20} />
                    <span>{isVi ? 'Hỏi AI ngay' : 'Ask AI Guide'}</span>
                </button>
            </div>

            {!isPhoneFrame && (
              <div style={{ marginTop: '20px' }}>
                <button className={styles.btnSecondary} onClick={openPhonePreview} style={{ fontSize: '14px', padding: '10px 20px' }}>
                  <Smartphone size={18} />
                  <span>{copy.secondary}</span>
                </button>
              </div>
            )}
            
            <div className={styles.heroRoute} aria-label={copy.heroMeta}>
              <MapPin size={16} />
              <span>{copy.heroMeta}</span>
            </div>
          </div>
        </section>

        <DestinationGrid
          destinations={destinations}
          language={language}
          onSelectDestination={handleDestinationSelect}
          kicker={copy.destinationKicker}
          title={copy.destinationTitle}
          description={copy.destinationText}
        />


        <footer className={styles.footer}>
          <div className={styles.footerBrand}>
            <div className={styles.logoMark}><span>AI</span></div>
            <div>
              <strong>AITourGuide</strong>
              <p>{copy.footerNote}</p>
            </div>
          </div>
          <div className={styles.footerContact}>
            <strong>{copy.contactTitle}</strong>
            <p>{copy.contactText}</p>
            <span>{isVi ? '17 điểm dừng chính trong Đại Nội Huế' : '17 main stops inside Hue Imperial City'}</span>
            <span>{isVi ? 'Bản đồ, hỏi đáp, nhận diện ảnh và thuyết minh giọng nói' : 'Map, Q&A, image recognition, and spoken narration'}</span>
          </div>
          <div className={styles.footerSources}>
            <strong>{isVi ? 'Nguồn ảnh' : 'Image sources'}</strong>
            <span>{isVi ? 'Ảnh công trình thuộc bộ nội dung của ứng dụng AI Tour Guide Đại Nội Huế' : 'Monument photos are part of the AI Tour Guide Hue Imperial City content set'}</span>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default HomeScreen;
