import React, { useRef, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Square } from 'lucide-react';
import type { GeoJSON } from '@/types';
import { fixLeafletIcons } from '@/lib/leaflet-config';

import 'leaflet-draw/dist/leaflet.draw.css';
fixLeafletIcons();

interface ZoneMapProps {
  zones: GeoJSON;
  selectedZoneId: string | null;
  isDrawingMode: boolean;
  onZoneClick: (feature: any, layer: any) => void;
  onDrawingModeToggle: () => void;
  onDrawCreated: (e: any) => void;
  onDrawEdited: (e: any) => void;
  onDrawDeleted: (e: any) => void;
  drawnItemsRef: React.MutableRefObject<L.FeatureGroup | null>;
  drawControlRef: React.MutableRefObject<L.Control.Draw | null>;
}

export function ZoneMap({
  zones,
  selectedZoneId,
  isDrawingMode,
  onZoneClick,
  onDrawingModeToggle,
  onDrawCreated,
  onDrawEdited,
  onDrawDeleted,
  drawnItemsRef,
  drawControlRef
}: ZoneMapProps) {
  const mapRef = useRef<L.Map | null>(null);

  // Initialize drawing controls when map is ready
  useEffect(() => {
    if (!mapRef.current || drawnItemsRef.current) return;

    const map = mapRef.current;
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    drawnItemsRef.current = drawnItems;

    // Add existing zones to drawn items for editing
    zones.features.forEach(feature => {
      const layer = L.geoJSON(feature.geometry as any, {
        style: {
          color: '#3388ff',
          weight: 2,
          fillOpacity: 0.2
        }
      });

      layer.eachLayer((l) => {
        (l as any).feature = feature;
        drawnItems.addLayer(l);
      });
    });

    return () => {
      if (map && drawnItems) {
        map.removeLayer(drawnItems);
      }
    };
  }, [mapRef.current, zones]);

  const getZoneStyle = (feature: any) => {
    const isSelected = feature.properties.id === selectedZoneId;
    return {
      fillColor: isSelected ? '#3b82f6' : '#6b7280',
      weight: isSelected ? 3 : 2,
      opacity: 1,
      color: isSelected ? '#1e40af' : 'white',
      fillOpacity: isSelected ? 0.5 : 0.3,
    };
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div>
            Zone Map
            {isDrawingMode && (
              <p className="text-sm text-muted-foreground font-normal mt-1">
                Click the rectangle tool and drag to draw a new zone
              </p>
            )}
          </div>
          <Button
            onClick={onDrawingModeToggle}
            variant={isDrawingMode ? "default" : "outline"}
            className={isDrawingMode ? "bg-green-600 hover:bg-green-700" : ""}
          >
            <Square className="h-4 w-4 mr-2" />
            {isDrawingMode ? "Exit Drawing" : "Draw Zone"}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[600px]">
          <MapContainer
            ref={mapRef}
            center={[40.4167, -3.7033]}
            zoom={12}
            className="h-full w-full"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <GeoJSON
              data={zones as any}
              style={getZoneStyle}
              onEachFeature={(feature, layer) => {
                layer.on({
                  click: () => onZoneClick(feature, layer)
                });

                if (feature.properties.id === selectedZoneId) {
                  layer.bindPopup(`
                    <div class="p-2">
                      <h3 class="font-semibold">${feature.properties.name}</h3>
                      <p class="text-sm">ID: ${feature.properties.id}</p>
                      <p class="text-sm">Population: ${feature.properties.population.toLocaleString()}</p>
                    </div>
                  `).openPopup();
                }
              }}
            />
          </MapContainer>
        </div>
      </CardContent>
    </Card>
  );
}