import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet-imageoverlay-rotated';

const RotatedImageOverlay = ({ url, topleft, topright, bottomleft, opacity = 1 }) => {
  const map = useMap();
  const overlayRef = useRef(null);

  useEffect(() => {
    // Only create the overlay if we have valid coordinates
    if (!topleft || !topright || !bottomleft || !topleft[0]) return;

    const overlay = L.imageOverlay.rotated(
      url, 
      L.latLng(topleft[0], topleft[1]), 
      L.latLng(topright[0], topright[1]), 
      L.latLng(bottomleft[0], bottomleft[1]), 
      {
        opacity,
        interactive: true
      }
    );
    overlay.addTo(map);
    overlayRef.current = overlay;

    return () => {
      if (overlayRef.current) {
        map.removeLayer(overlayRef.current);
      }
    };
  }, [map, url]);

  useEffect(() => {
    if (overlayRef.current && topleft && topright && bottomleft && topleft[0]) {
      overlayRef.current.reposition(
        L.latLng(topleft[0], topleft[1]), 
        L.latLng(topright[0], topright[1]), 
        L.latLng(bottomleft[0], bottomleft[1])
      );
      overlayRef.current.setOpacity(opacity);
    }
  }, [topleft, topright, bottomleft, opacity]);

  return null;
};

export default RotatedImageOverlay;
