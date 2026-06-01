import React, { useEffect, useRef, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  Compass,
  Landmark,
  MapPin,
  MessageCircle,
  Mic,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Volume2
} from 'lucide-react';

const REAL_IMAGES = {
  hue: 'https://commons.wikimedia.org/wiki/Special:FilePath/Meridian%20Gate%2C%20Hue%20%28I%29.jpg',
  palace: 'https://images.pexels.com/photos/20051245/pexels-photo-20051245.jpeg?auto=compress&cs=tinysrgb&w=1800',
  museum: 'https://commons.wikimedia.org/wiki/Special:FilePath/Ho%20Chi%20Minh%20City%2C%20Vietnam%2C%20War%20Remnants%20Museum.jpg'
};

const HomeScreen = ({ onSelectFeature, language, setLanguage }) => {
  const isVi = language === 'vi';
  const [activeScene, setActiveScene] = useState('hue');
  const [visibleIds, setVisibleIds] = useState(() => new Set(['hero']));
  const [isLaunching, setIsLaunching] = useState(false);
  const rootRef = useRef(null);
  const carouselRef = useRef(null);
  const dragStateRef = useRef({ active: false, startX: 0, scrollLeft: 0 });
  const sectionRefs = useRef({});

  const copy = {
    eyebrow: isVi ? 'AI Tour Guide cho di sản Việt Nam' : 'AI Tour Guide for Vietnamese heritage',
    title: isVi
      ? 'Biến mỗi điểm dừng thành một câu chuyện sống động.'
      : 'Turn every stop into a living story.',
    desc: isVi
      ? 'Khách tham quan chỉ cần đưa ảnh, nói một câu hỏi hoặc chọn địa điểm. AI Tour Guide trả lời ngắn, đúng ngữ cảnh và có thể đọc thành lời.'
      : 'Visitors can share a photo, ask by voice, or choose a place. AI Tour Guide answers concisely, in context, and can speak the guide back.',
    primary: isVi ? 'Bắt đầu trải nghiệm' : 'Start the experience',
    secondary: isVi ? 'Xem hành trình' : 'See the journey',
    navPlaces: isVi ? 'Địa danh' : 'Places',
    navFeatures: isVi ? 'Tính năng' : 'Features',
    heroMeta: isVi ? 'Huế - Dinh Độc Lập - Chứng tích Chiến tranh' : 'Hue - Independence Palace - War Remnants',
    storyKicker: isVi ? 'Kéo xuống để đi qua hành trình' : 'Scroll through the journey',
    storyTitle: isVi
      ? 'Không phải một chatbot trong hộp thoại. Đây là lớp thuyết minh đi cùng không gian.'
      : 'Not a chatbot trapped in a box. A guide layer that follows the space.',
    featureKicker: isVi ? 'Chức năng xuất hiện đúng lúc' : 'Features that appear at the right moment',
    featureTitle: isVi
      ? 'Người tham quan không cần học cách dùng app.'
      : 'Visitors do not need to learn the app.',
    outcomeKicker: isVi ? 'Thiết kế cho chuyến tham quan thật' : 'Designed for real visits',
    outcomeTitle: isVi
      ? 'Mượt, dễ nhìn và tập trung vào câu hỏi của người dùng.'
      : 'Smooth, clear, and focused on the visitor question.',
    finalTitle: isVi ? 'Sẵn sàng bước vào không gian demo.' : 'Ready to enter the demo space.',
    finalText: isVi
      ? 'Bắt đầu với một câu hỏi, một bức ảnh hoặc giọng nói. Phần còn lại để AI Tour Guide dẫn mạch.'
      : 'Start with a question, photo, or voice note. Let AI Tour Guide carry the thread from there.',
    contactTitle: isVi ? 'Liên hệ và nội dung tùy chỉnh' : 'Contact and editable content',
    contactText: isVi
      ? 'Thay các dòng này bằng email, hotline, đơn vị triển khai, tài liệu hướng dẫn hoặc thông tin demo của bạn.'
      : 'Replace these lines with email, hotline, deployment owner, docs, or demo information.',
    footerNote: isVi
      ? 'Ghi chú: ảnh địa danh đang dùng nguồn công khai, bạn có thể thay bằng ảnh tự chụp trong thư mục assets.'
      : 'Note: landmark images use public sources; you can replace them with your own photos in assets.',
    launchText: isVi ? 'Đang mở không gian thuyết minh' : 'Opening the guide space',
    scenes: [
      {
        id: 'hue',
        image: REAL_IMAGES.hue,
        place: isVi ? 'Kinh thành Huế' : 'Hue Imperial City',
        eyebrow: isVi ? 'Điểm dừng 01' : 'Stop 01',
        title: isVi ? 'Chụp một chi tiết, nghe cả bối cảnh.' : 'Capture one detail, hear the full context.',
        text: isVi
          ? 'Từ Ngọ Môn, Điện Thái Hòa đến Cửu Đỉnh, hệ thống gom dữ liệu hiện vật và trả lời theo mạch tham quan.'
          : 'From Ngo Mon Gate and Thai Hoa Palace to the Nine Dynastic Urns, the system keeps artifact context tied to the visit.',
        prompt: isVi ? 'Kể ngắn về Cửu Đỉnh trong 30 giây' : 'Summarize the Nine Dynastic Urns in 30 seconds',
        chips: isVi ? ['Ảnh hiện vật', 'Bối cảnh lịch sử', 'Song ngữ'] : ['Artifact photo', 'Historical context', 'Bilingual']
      },
      {
        id: 'palace',
        image: REAL_IMAGES.palace,
        place: isVi ? 'Dinh Độc Lập' : 'Independence Palace',
        eyebrow: isVi ? 'Điểm dừng 02' : 'Stop 02',
        title: isVi ? 'Hỏi tự nhiên khi đang di chuyển.' : 'Ask naturally while moving.',
        text: isVi
          ? 'Người dùng có thể hỏi bằng giọng nói về Phòng Nội các, Hầm chỉ huy hoặc Xe tăng 843 mà không phải dừng lại đọc dài.'
          : 'Visitors can ask by voice about the Cabinet Room, Command Bunker, or Tank 843 without stopping to read long labels.',
        prompt: isVi ? 'Ý nghĩa lịch sử của Dinh Độc Lập là gì?' : 'What is the historical meaning of Independence Palace?',
        chips: isVi ? ['Giọng nói', 'Hỏi đáp nhanh', 'TTS'] : ['Voice', 'Quick Q&A', 'TTS']
      },
      {
        id: 'museum',
        image: REAL_IMAGES.museum,
        place: isVi ? 'Bảo tàng Chứng tích Chiến tranh' : 'War Remnants Museum',
        eyebrow: isVi ? 'Điểm dừng 03' : 'Stop 03',
        title: isVi ? 'Giữ câu trả lời nhạy cảm, ngắn gọn và đúng trọng tâm.' : 'Keep sensitive answers concise and focused.',
        text: isVi
          ? 'Với các chủ đề lịch sử nặng, giao diện ưu tiên giọng văn rõ ràng, có kiểm soát và cho phép phản hồi nếu câu trả lời chưa phù hợp.'
          : 'For heavier historical topics, the interface prioritizes careful wording and lets visitors give feedback when an answer misses the mark.',
        prompt: isVi ? 'Giải thích ngắn về F-5E Tiger' : 'Give a short explanation of the F-5E Tiger',
        chips: isVi ? ['Phản hồi', 'Giọng văn rõ', 'Lưu mạch chat'] : ['Feedback', 'Clear tone', 'Conversation memory']
      }
    ],
    features: [
      {
        icon: ScanSearch,
        title: isVi ? 'Nhìn hiện vật' : 'See the artifact',
        text: isVi ? 'Upload hoặc webcam khởi tạo phần thuyết minh theo ảnh.' : 'Upload or webcam starts the guide from the image.'
      },
      {
        icon: Mic,
        title: isVi ? 'Hỏi bằng lời' : 'Ask by voice',
        text: isVi ? 'Câu hỏi tự nhiên phù hợp lúc đang đi trong không gian trưng bày.' : 'Natural questions for people walking through an exhibit.'
      },
      {
        icon: MessageCircle,
        title: isVi ? 'Đào sâu ngữ cảnh' : 'Go deeper',
        text: isVi ? 'Hỏi tiếp về niên đại, nhân vật, địa điểm hoặc ý nghĩa lịch sử.' : 'Follow up on period, people, place, or historical meaning.'
      },
      {
        icon: Volume2,
        title: isVi ? 'Nghe thuyết minh' : 'Hear narration',
        text: isVi ? 'Câu trả lời có thể phát thành âm thanh khi người dùng không muốn đọc.' : 'Answers can play as audio when reading is inconvenient.'
      }
    ],
    outcomes: [
      {
        icon: Landmark,
        title: isVi ? 'Cho bảo tàng và di tích' : 'For museums and heritage sites',
        text: isVi ? 'Giảm cảm giác lạc hướng, tăng khả năng tự khám phá.' : 'Reduce friction and make self-guided visits feel supported.'
      },
      {
        icon: BookOpen,
        title: isVi ? 'Cho học tập lịch sử' : 'For history learning',
        text: isVi ? 'Chuyển dữ liệu hiện vật thành câu chuyện ngắn, dễ nhớ.' : 'Turn artifact data into short, memorable explanations.'
      },
      {
        icon: ShieldCheck,
        title: isVi ? 'Cho demo AI có kiểm soát' : 'For controlled AI demos',
        text: isVi ? 'Một luồng thể hiện đủ ảnh, giọng nói, hội thoại và phản hồi.' : 'One flow shows image, voice, chat, and feedback together.'
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
      onSelectFeature('chat');
    }, 720);
  };

  const startMapExperience = () => {
    if (isLaunching) return;
    setIsLaunching(true);
    window.setTimeout(() => {
      onSelectFeature('map');
    }, 720);
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
                <div 
                    className="location-card-hero" 
                    onClick={() => onSelectFeature('dashboard', { id: 1, name_vi: "Kinh thành Huế (Đại Nội)" })}
                    style={{
                        background: 'rgba(255,255,255,0.12)',
                        backdropFilter: 'blur(12px)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        borderRadius: '24px',
                        padding: '24px',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '20px',
                        maxWidth: '480px',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
                    }}
                >
                    <div style={{ width: '70px', height: '70px', borderRadius: '16px', background: '#0f5f59', display: 'grid', placeItems: 'center', boxShadow: '0 8px 20px rgba(15,95,89,0.3)' }}>
                        <Landmark size={36} color="#fff" />
                    </div>
                    <div style={{ textAlign: 'left' }}>
                        <h3 style={{ margin: 0, color: '#fff', fontSize: '20px', fontWeight: '700' }}>{isVi ? 'Kinh thành Huế' : 'Hue Imperial City'}</h3>
                        <p style={{ margin: '4px 0 0', color: 'rgba(255,255,255,0.8)', fontSize: '13px' }}>{isVi ? 'Đại Nội – Di sản Văn hóa Thế giới UNESCO' : 'The Citadel – UNESCO World Heritage Site'}</p>
                        <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '6px', color: '#fece14' }}>
                            <span style={{ fontSize: '14px', fontWeight: 'bold' }}>{isVi ? 'Bắt đầu khám phá' : 'Start exploring'}</span>
                            <ArrowRight size={16} />
                        </div>
                    </div>
                </div>
            </div>
            
            <div className="hero-route" aria-label={copy.heroMeta} style={{ marginTop: '30px' }}>
              <MapPin size={16} />
              <span>{copy.heroMeta}</span>
            </div>
          </div>
        </section>

        <section className="landing-story-shell" id="places">
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
            <span className="section-label">{isVi ? 'Không gian demo' : 'Demo workspace'}</span>
            <h2>{copy.finalTitle}</h2>
            <p>{copy.finalText}</p>
          </div>
          <button className="primary" onClick={() => onSelectFeature('dashboard', { id: 1, name_vi: "Kinh thành Huế (Đại Nội)" })}>
            <span>{copy.primary}</span>
            <ArrowRight size={18} />
          </button>
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
            <span>Email: hello@example.com</span>
            <span>Hotline: +84 000 000 000</span>
          </div>
          <div className="footer-sources">
            <strong>{isVi ? 'Nguồn ảnh' : 'Image sources'}</strong>
            <a href="https://commons.wikimedia.org/wiki/File:Meridian_Gate,_Hue_(I).jpg" target="_blank" rel="noreferrer">Hue Imperial City / Wikimedia Commons</a>
            <a href="https://www.pexels.com/photo/independence-palace-in-ho-chi-minh-20051245/" target="_blank" rel="noreferrer">Independence Palace / Pexels</a>
            <a href="https://commons.wikimedia.org/wiki/File:Ho_Chi_Minh_City,_Vietnam,_War_Remnants_Museum.jpg" target="_blank" rel="noreferrer">War Remnants Museum / Wikimedia Commons</a>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default HomeScreen;
