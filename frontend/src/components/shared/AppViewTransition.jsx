import React, { useEffect, useRef, useState } from 'react';

const TRANSITION_MS = 260;
const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)';

const usePrefersReducedMotion = () => {
  const [reduced, setReduced] = useState(() => (
    typeof window !== 'undefined'
      ? window.matchMedia(REDUCED_MOTION_QUERY).matches
      : false
  ));

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const mediaQuery = window.matchMedia(REDUCED_MOTION_QUERY);
    const handleChange = () => setReduced(mediaQuery.matches);

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  return reduced;
};

const AppViewTransition = ({ viewKey, children }) => {
  const reducedMotion = usePrefersReducedMotion();
  const transitionIdRef = useRef(0);
  const [views, setViews] = useState(() => ([{
    id: 0,
    key: viewKey,
    element: children,
    phase: 'enter'
  }]));

  useEffect(() => {
    if (reducedMotion) {
      transitionIdRef.current += 1;
      setViews([{
        id: transitionIdRef.current,
        key: viewKey,
        element: children,
        phase: 'enter'
      }]);
      return undefined;
    }

    setViews((currentViews) => {
      const activeView = currentViews[currentViews.length - 1];
      if (activeView?.key === viewKey) {
        return currentViews.map((view, index) => (
          index === currentViews.length - 1
            ? { ...view, element: children }
            : view
        ));
      }

      transitionIdRef.current += 1;
      const outgoingView = activeView
        ? [{ ...activeView, phase: 'exit' }]
        : [];

      return [
        ...outgoingView,
        {
          id: transitionIdRef.current,
          key: viewKey,
          element: children,
          phase: 'enter'
        }
      ];
    });

    const cleanupTimer = window.setTimeout(() => {
      setViews((currentViews) => {
        const activeView = currentViews[currentViews.length - 1];
        return activeView ? [{ ...activeView, phase: 'enter' }] : currentViews;
      });
    }, TRANSITION_MS + 40);

    return () => window.clearTimeout(cleanupTimer);
  }, [children, reducedMotion, viewKey]);

  return (
    <div className="app-view-transition-stage" aria-live="polite">
      {views.map((view, index) => (
        <div
          className={`app-view-transition-layer is-${view.phase}`}
          data-active={index === views.length - 1 ? 'true' : 'false'}
          key={`${view.key}-${view.id}`}
        >
          {view.element}
        </div>
      ))}
    </div>
  );
};

export default AppViewTransition;
