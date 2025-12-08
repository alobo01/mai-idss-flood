import L from 'leaflet';
import type { GeoJSON } from '@/types';

interface ZoneDrawControlsProps {
  map: L.Map;
  isDrawingMode: boolean;
  setIsDrawingMode: (mode: boolean) => void;
  drawnItems: L.FeatureGroup;
  onDrawCreated: (e: any) => void;
  onDrawEdited: (e: any) => void;
  onDrawDeleted: (e: any) => void;
  drawControlRef: React.MutableRefObject<L.Control.Draw | null>;
}

export const setupDrawControls = ({
  map,
  isDrawingMode,
  setIsDrawingMode,
  drawnItems,
  onDrawCreated,
  onDrawEdited,
  onDrawDeleted,
  drawControlRef
}: ZoneDrawControlsProps) => {
  if (isDrawingMode) {
    // Exit drawing mode
    setIsDrawingMode(false);
    if (drawControlRef.current) {
      map.removeControl(drawControlRef.current);
      drawControlRef.current = null;
    }
  } else {
    // Enter drawing mode
    setIsDrawingMode(true);

    const drawControl = new L.Control.Draw({
      draw: {
        polygon: {
          allowIntersection: false,
          showArea: true,
          drawError: {
            color: '#e1e100',
            message: '<strong>Error:</strong> Shape edges cannot cross!'
          },
          shapeOptions: {
            color: '#3b82f6',
            weight: 3,
            fillOpacity: 0.3,
            fillColor: '#3b82f6'
          }
        },
        polyline: false,
        circle: false,
        circlemarker: false,
        rectangle: {
          showArea: true,
          shapeOptions: {
            color: '#10b981',
            weight: 3,
            fillOpacity: 0.3,
            fillColor: '#10b981'
          }
        },
        marker: false
      },
      edit: {
        featureGroup: drawnItems,
        remove: true,
        edit: {
          selectedPathOptions: {
            color: '#f59e0b',
            weight: 3,
            fillOpacity: 0.4,
            fillColor: '#f59e0b'
          }
        }
      }
    });

    map.addControl(drawControl);
    drawControlRef.current = drawControl;

    // Handle draw events
    map.on(L.Draw.Event.CREATED, onDrawCreated);
    map.on(L.Draw.Event.EDITED, onDrawEdited);
    map.on(L.Draw.Event.DELETED, onDrawDeleted);
  }
};

export const generateZoneId = (zones: GeoJSON): string => {
  const existingIds = zones.features.map(f => f.properties.id);
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let counter = 0;

  while (counter < 26) {
    const id = `Z-${letters[counter]}`;
    if (!existingIds.includes(id)) {
      return id;
    }
    counter++;
  }

  // If all single letters are used, use double letters
  let suffix = 1;
  while (true) {
    const id = `Z-${letters[0]}${suffix}`;
    if (!existingIds.includes(id)) {
      return id;
    }
    suffix++;
  }
};