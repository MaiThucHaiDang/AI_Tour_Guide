import React, { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import HomeScreen from './components/HomeScreen';
import AppViewTransition from './components/shared/AppViewTransition';
import { getDestinationById } from './data/destinations';

const lazyWithPreload = (factory) => {
  let modulePromise;
  const load = () => {
    modulePromise ||= factory();
    return modulePromise;
  };
  const Component = lazy(load);
  Component.preload = load;
  return Component;
};

const ExploreDashboard = lazyWithPreload(() => import('./components/dashboard/ExploreDashboard'));
const MapCalibrate = lazyWithPreload(() => import('./components/map/MapCalibrate'));
const PhonePreview = lazyWithPreload(() => import('./components/PhonePreview'));
const GamePlayer = lazyWithPreload(() => import('./components/game/GamePlayer'));
const DestinationDetail = lazyWithPreload(() => import('./components/destinations/DestinationDetail'));
const BlogListPage = lazyWithPreload(() => import('./components/blog/BlogListPage'));
const BlogDetailPage = lazyWithPreload(() => import('./components/blog/BlogDetailPage'));
const BlogEditorPage = lazyWithPreload(() => import('./components/blog/BlogEditorPage'));
const PaymentResult = lazyWithPreload(() => import('./components/payment/PaymentResult'));

const DEFAULT_TOUR_LOCATION = {
  id: 1,
  name_vi: 'Kinh thành Huế (Đại Nội)',
  name_en: 'Hue Imperial City'
};

const VIEW_PRELOADERS = {
  dashboard: ExploreDashboard.preload,
  calibrate: MapCalibrate.preload,
  phone: PhonePreview.preload,
  join: GamePlayer.preload,
  destination: DestinationDetail.preload,
  blog: BlogListPage.preload,
  blogDetail: BlogDetailPage.preload,
  blogNew: BlogEditorPage.preload,
  paymentResult: PaymentResult.preload
};

const preloadView = (view) => {
  VIEW_PRELOADERS[view]?.();
};

const AppRouteLoader = ({ language }) => {
  const isVi = language === 'vi';
  return (
    <div className="app-route-loader" role="status" aria-live="polite">
      <span className="app-route-loader-mark" aria-hidden="true" />
      <strong>{isVi ? 'Đang mở trải nghiệm...' : 'Opening experience...'}</strong>
    </div>
  );
};

const updateViewQuery = (view, params = {}) => {
  const url = new URL(window.location.href);
  url.pathname = '/';
  url.searchParams.delete('destination');
  if (view === 'home') {
    url.searchParams.delete('view');
  } else {
    url.searchParams.set('view', view);
  }
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  });
  window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
};

const getBlogRouteFromPath = () => {
  const cleanPath = window.location.pathname.replace(/\/+$/, '') || '/';
  if (cleanPath === '/blog') {
    return { view: 'blog', slug: null };
  }
  if (cleanPath === '/blog/new') {
    return { view: 'blogNew', slug: null };
  }
  if (cleanPath.startsWith('/blog/')) {
    const slug = decodeURIComponent(cleanPath.replace('/blog/', '')).trim();
    return slug ? { view: 'blogDetail', slug } : { view: 'blog', slug: null };
  }
  return null;
};

const destinationToTourArtifact = (destination, language) => ({
  id: destination.artifactId || destination.id,
  name_vi: destination.nameVi,
  name_en: destination.nameEn,
  year: destination.year,
  author: language === 'vi' ? destination.authorVi : destination.authorEn,
  summary: language === 'vi' ? destination.summaryVi : destination.summaryEn,
  lat: destination.lat,
  lng: destination.lng
});

const getInitialDestinationFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  return getDestinationById(params.get('destination'));
};

function App() {
  const isPhoneFrame = new URLSearchParams(window.location.search).get('frame') === 'phone';
  const initialBlogRoute = getBlogRouteFromPath();
  const [appState, setAppState] = useState(() => {
    if (initialBlogRoute) return initialBlogRoute.view;
    const view = new URLSearchParams(window.location.search).get('view');
    if (view === 'calibrate') return 'calibrate';
    if (view === 'phone') return 'phone';
    if (view === 'join') return 'join';
    if (view === 'destination' && getInitialDestinationFromUrl()) return 'destination';
    if (view === 'paymentResult') return 'paymentResult';
    return view === 'dashboard' ? 'dashboard' : 'home';
  });
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('ai_tour_lang') || 'vi';
  });
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState(() => {
    return getInitialDestinationFromUrl();
  });
  const [selectedBlogSlug, setSelectedBlogSlug] = useState(() => {
    return initialBlogRoute?.slug || null;
  });

  useEffect(() => {
    localStorage.setItem('ai_tour_lang', language);
  }, [language]);

  useEffect(() => {
    const syncRouteFromLocation = () => {
      const blogRoute = getBlogRouteFromPath();
      if (blogRoute) {
        preloadView(blogRoute.view);
        setSelectedBlogSlug(blogRoute.slug);
        setSelectedLocation(null);
        setSelectedDestination(null);
        setAppState(blogRoute.view);
        return;
      }

      const params = new URLSearchParams(window.location.search);
      const view = params.get('view');
      const destination = view === 'destination' ? getDestinationById(params.get('destination')) : null;
      setSelectedBlogSlug(null);
      setSelectedDestination(destination);
      if (view === 'calibrate') {
        preloadView('calibrate');
        setAppState('calibrate');
      } else if (view === 'phone') {
        preloadView('phone');
        setAppState('phone');
      } else if (view === 'join') {
        preloadView('join');
        setAppState('join');
      } else if (view === 'destination' && destination) {
        preloadView('destination');
        setAppState('destination');
      } else if (view === 'paymentResult') {
        preloadView('paymentResult');
        setAppState('paymentResult');
      } else if (view === 'dashboard') {
        preloadView('dashboard');
        setAppState('dashboard');
      } else {
        setAppState('home');
      }
    };

    window.addEventListener('popstate', syncRouteFromLocation);
    return () => window.removeEventListener('popstate', syncRouteFromLocation);
  }, []);

  const resetToHome = () => {
    setAppState('home');
    setSelectedLocation(null);
    setSelectedDestination(null);
    setSelectedBlogSlug(null);
    updateViewQuery('home');
  };

  const backToDestinationList = () => {
    resetToHome();
    window.setTimeout(() => {
      document.getElementById('places')?.scrollIntoView({ block: 'start' });
    }, 0);
  };

  const handleSelectLocation = (location) => {
    preloadView('dashboard');
    setSelectedLocation(location);
    setAppState('dashboard');
    updateViewQuery('dashboard');
  };

  const handleSelectDestination = (destination) => {
    preloadView('destination');
    setSelectedDestination(destination);
    setAppState('destination');
    updateViewQuery('destination', { destination: destination.id });
  };

  const handleStartDestinationTour = (destination, initialTab = 'map') => {
    preloadView('dashboard');
    setSelectedLocation({
      id: destination.id,
      type: 'destination',
      name_vi: destination.nameVi,
      name_en: destination.nameEn,
      initialTab,
      initialArtifact: destinationToTourArtifact(destination, language),
      selectedAt: Date.now()
    });
    setAppState('dashboard');
    updateViewQuery('dashboard');
  };

  const handleOpenPhonePreview = (data) => {
    preloadView('phone');
    setSelectedLocation({
      ...DEFAULT_TOUR_LOCATION,
      ...(data || {}),
      initialTab: data?.initialTab || 'map'
    });
    setAppState('phone');
    updateViewQuery('phone');
  };

  const openBlogList = () => {
    preloadView('blog');
    setSelectedLocation(null);
    setSelectedDestination(null);
    setSelectedBlogSlug(null);
    setAppState('blog');
    window.history.pushState(null, '', '/blog');
  };

  const openBlogDetail = (slug) => {
    preloadView('blogDetail');
    setSelectedLocation(null);
    setSelectedDestination(null);
    setSelectedBlogSlug(slug);
    setAppState('blogDetail');
    window.history.pushState(null, '', `/blog/${encodeURIComponent(slug)}`);
  };

  const openBlogEditor = () => {
    preloadView('blogNew');
    setSelectedLocation(null);
    setSelectedDestination(null);
    setSelectedBlogSlug(null);
    setAppState('blogNew');
    window.history.pushState(null, '', '/blog/new');
  };

  const transitionKey = useMemo(() => {
    if (appState === 'blogDetail') return `${appState}:${selectedBlogSlug || ''}`;
    if (appState === 'destination') return `${appState}:${selectedDestination?.id || ''}`;
    return appState;
  }, [appState, selectedBlogSlug, selectedDestination?.id]);

  const currentView = (
    <>
      {appState === 'home' && (
        <HomeScreen
          onSelectFeature={(feature, data) => {
            if (feature === 'phone') {
              if (isPhoneFrame) {
                handleSelectLocation({ ...DEFAULT_TOUR_LOCATION, ...(data || {}), initialTab: 'map' });
                return;
              }
              handleOpenPhonePreview(data);
              return;
            }

            if (feature === 'dashboard' || feature === 'chat' || feature === 'map') {
              handleSelectLocation({
                ...DEFAULT_TOUR_LOCATION,
                ...(data || {}),
                initialTab: feature === 'chat' ? 'ask' : 'map'
              });
            }
          }}
          language={language}
          setLanguage={setLanguage}
          isPhoneFrame={isPhoneFrame}
          onSelectDestination={handleSelectDestination}
          onOpenBlog={openBlogList}
        />
      )}

      {appState === 'destination' && selectedDestination && (
        <DestinationDetail
          destination={selectedDestination}
          language={language}
          onBack={backToDestinationList}
          onStartTour={(destination) => handleStartDestinationTour(destination, 'map')}
          onAskGuide={(destination) => handleStartDestinationTour(destination, 'ask')}
        />
      )}

      {appState === 'dashboard' && (
        <ExploreDashboard
          onBack={resetToHome}
          language={language}
          setLanguage={setLanguage}
          initialLocation={selectedLocation}
        />
      )}

      {appState === 'calibrate' && (
        <MapCalibrate
          onBack={resetToHome}
          language={language}
        />
      )}

      {appState === 'phone' && (
        <PhonePreview
          onBack={resetToHome}
          language={language}
        />
      )}

      {appState === 'join' && (
        <GamePlayer
          roomCode={new URLSearchParams(window.location.search).get('code') || ''}
          language={language}
          onBack={resetToHome}
        />
      )}

      {appState === 'blog' && (
        <BlogListPage
          language={language}
          onBackHome={resetToHome}
          onOpenBlogDetail={openBlogDetail}
          onCreatePost={openBlogEditor}
        />
      )}

      {appState === 'blogDetail' && selectedBlogSlug && (
        <BlogDetailPage
          slug={selectedBlogSlug}
          language={language}
          onBackList={openBlogList}
        />
      )}

      {appState === 'blogNew' && (
        <BlogEditorPage
          language={language}
          onBackList={openBlogList}
          onPostCreated={openBlogDetail}
        />
      )}

      {appState === 'paymentResult' && (
        <PaymentResult
          language={language}
          onBack={resetToHome}
        />
      )}
    </>
  );

  return (
    <div
      className={`app-root ${isPhoneFrame ? 'is-phone-frame' : ''}`}
      style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}
    >
      <AppViewTransition viewKey={transitionKey}>
        <Suspense fallback={<AppRouteLoader language={language} />}>
          {currentView}
        </Suspense>
      </AppViewTransition>
    </div>
  );
}

export default App;
