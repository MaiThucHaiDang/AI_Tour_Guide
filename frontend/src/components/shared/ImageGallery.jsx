import React, { useState, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

export default function ImageGallery({ images, className = '', imgClassName = '', clipContainer = '' }) {
  const [lightboxIndex, setLightboxIndex] = useState(null);
  const [clipRect, setClipRect] = useState(null);
  const rafRef = useRef(null);

  const open = useCallback((i) => setLightboxIndex(i), []);
  const close = useCallback(() => { setLightboxIndex(null); setClipRect(null); }, []);

  useEffect(() => {
    if (lightboxIndex !== null) {
      const handler = (e) => { if (e.key === 'Escape') close(); };
      window.addEventListener('keydown', handler);
      return () => window.removeEventListener('keydown', handler);
    }
  }, [lightboxIndex, close]);

  useEffect(() => {
    if (lightboxIndex === null || !clipContainer) return;
    const update = () => {
      const el = document.querySelector(clipContainer);
      if (el) {
        const r = el.getBoundingClientRect();
        setClipRect({ top: r.top, left: r.left, width: r.width, height: r.height });
      }
    };
    update();
    const onResize = () => { rafRef.current = requestAnimationFrame(update); };
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [lightboxIndex, clipContainer]);

  if (!images || images.length === 0) return null;

  const overlayStyle = clipRect
    ? { position: 'fixed', top: clipRect.top, left: clipRect.left, width: clipRect.width, height: clipRect.height }
    : {};

  const imgMaxStyle = clipRect
    ? { width: `${clipRect.width * 0.75}px`, height: `${clipRect.height * 0.75}px` }
    : {};

  return (
    <>
      <div className={`${className}`}>
        {images.map((src, i) => (
          <img
            key={i}
            src={src}
            alt={`Image ${i + 1}`}
            className={`${imgClassName} gallery-clickable`}
            onClick={() => open(i)}
          />
        ))}
      </div>

      {lightboxIndex !== null && createPortal(
        <div className={`gallery-overlay ${clipRect ? 'gallery-overlay-clip' : ''}`} style={overlayStyle} onClick={close}>
          <div className="gallery-overlay-content" onClick={(e) => e.stopPropagation()}>
            <button className="gallery-overlay-close" onClick={close}>&times;</button>
            <img
              src={images[lightboxIndex]}
              alt={`Image ${lightboxIndex + 1}`}
              className="gallery-overlay-img"
              style={imgMaxStyle}
            />
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
