import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Layers, Clock, MapPin } from 'lucide-react';
import { PipelineRuleBasedAllocation } from '@/hooks/useRuleBased';
import type {
  GeoJSON as GeoJSONType,
  RiskPoint,
  ZoneProperties,
  Gauge,
  Alert
} from '@/types';
import { fixLeafletIcons } from '@/lib/leaflet-config';

// Initialize Leaflet icons once when module loads
fixLeafletIcons();

interface MapViewProps {
  zones: GeoJSONType;
  riskData?: RiskPoint[];
   ruleData?: PipelineRuleBasedAllocation[];
  selectedZone?: string | null;
  onZoneSelect?: (zoneId: string) => void;
  timeHorizon?: string;
  layers?: {
    zones: boolean;
    risk: boolean;
    rule: boolean;
    assets: boolean;
    gauges: boolean;
  };
  className?: string;
}

// Component to handle map events and bounds
const MapController: React.FC<{
  onZoneSelect?: (zoneId: string) => void;
  selectedZone?: string | null;
  zones: GeoJSONType;
}> = ({ onZoneSelect, selectedZone, zones }) => {
  const map = useMap();

  useEffect(() => {
    // Fit map to show all zones when data loads
    if (zones?.features?.length > 0) {
      try {
        const bounds = L.latLngBounds([]);
        zones.features.forEach((feature) => {
          if (feature.geometry?.coordinates?.[0]) {
            feature.geometry.coordinates[0].forEach((coord: number[]) => {
              bounds.extend([coord[1], coord[0]]);
            });
          }
        });

        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [20, 20] });
        }
      } catch (error) {
        console.warn('Could not fit map to bounds:', error);
        // Fall back to default center/zoom
      }
    }

    const handleClick = (e: any) => {
      // This will be handled by GeoJSON layer events
    };

    map.on('click', handleClick);
    return () => {
      map.off('click', handleClick);
    };
  }, [map, zones]);

  return null;
};

export function MapView({
  zones,
  riskData = [],
  ruleData = [],
  selectedZone,
  onZoneSelect,
  timeHorizon = '12h',
  layers = { zones: true, risk: true, rule: true, assets: true, gauges: true },
  className = ''
}: MapViewProps) {
  const [mapCenter] = useState<[number, number]>([38.627, -90.199]); // St. Louis
  const [mapZoom] = useState(12);

  // Validate zones data
  if (!zones || !zones.features || zones.features.length === 0) {
    return (
      <div className={className}>
        <Card className="overflow-hidden">
          <div className="h-[600px] flex items-center justify-center bg-gray-100 dark:bg-gray-800">
            <div className="text-center">
              <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-300">No zone data available</p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  // Get risk color based on value
  const getRiskColor = (riskValue: number): string => {
    if (riskValue >= 0.75) return '#ef4444'; // red-500
    if (riskValue >= 0.5) return '#f97316'; // orange-500
    if (riskValue >= 0.25) return '#eab308'; // yellow-500
    return '#22c55e'; // green-500
  };

  // Rule-based impact colors
  const getRuleColor = (impact?: string): string => {
    switch ((impact || '').toUpperCase()) {
      case 'CRITICAL':
        return '#b91c1c'; // red-700
      case 'WARNING':
        return '#f97316'; // orange-500
      case 'ADVISORY':
        return '#eab308'; // yellow-500
      case 'NORMAL':
        return '#22c55e'; // green-500
      default:
        return '#6b7280'; // gray-500 fallback
    }
  };

  // Style GeoJSON zones based on risk data
  const getZoneStyle = (feature: any) => {
    const zoneId = feature.properties.id;
    const rulePoint = ruleData.find(r => r.zone_id === zoneId);
    const riskPoint = riskData.find(r => r.zoneId === zoneId);

    if (layers.rule && rulePoint) {
      const fillColor = getRuleColor(rulePoint.impact_level);
      return {
        fillColor,
        weight: selectedZone === zoneId ? 3 : 2,
        opacity: 1,
        color: selectedZone === zoneId ? '#1f2937' : 'white',
        fillOpacity: selectedZone === zoneId ? 0.65 : 0.55,
      };
    }

    if (!layers.risk || !riskPoint) {
      return {
        fillColor: '#6b7280',
        weight: 2,
        opacity: 1,
        color: 'white',
        fillOpacity: layers.zones ? 0.3 : 0,
      };
    }

    const fillColor = getRiskColor(riskPoint.risk);

    return {
      fillColor,
      weight: selectedZone === zoneId ? 3 : 2,
      opacity: 1,
      color: selectedZone === zoneId ? '#1f2937' : 'white',
      fillOpacity: selectedZone === zoneId ? 0.7 : 0.5,
    };
  };

  // Handle zone click
  const handleZoneClick = (feature: any, layer: any) => {
    const zoneId = feature.properties.id;
    if (onZoneSelect) {
      onZoneSelect(zoneId);
    }

    // Bind popup to the layer
    const zoneName = feature.properties.name;
    const population = feature.properties.population;
    const rulePoint = ruleData.find(r => r.zone_id === zoneId);
    const riskPoint = riskData.find(r => r.zoneId === zoneId);

    let popupContent = `
      <div class="p-3 min-w-[200px]">
        <h3 class="font-semibold text-sm mb-2">${zoneName}</h3>
        <p class="text-xs text-gray-600 mb-2">Population: ${population.toLocaleString()}</p>
    `;

    if (rulePoint && layers.rule) {
      const ruleColor = getRuleColor(rulePoint.impact_level);
      popupContent += `
        <div class="mb-2">
          <span class="text-xs font-medium">Impact:</span>
          <span style="color: ${ruleColor}" class="ml-1 font-bold">${(rulePoint.impact_level || '').toUpperCase()}</span>
          <span class="text-xs ml-1 px-1 py-0.5 rounded" style="background-color: ${ruleColor}20">${rulePoint.allocation_mode}</span>
        </div>
        <div class="text-xs text-gray-600 space-y-1">
          <p>Units allocated: ${rulePoint.units_allocated}</p>
          ${rulePoint.pf !== undefined ? `<p>PF: ${(rulePoint.pf * 100).toFixed(0)}%</p>` : ''}
          ${rulePoint.vulnerability !== undefined ? `<p>Vulnerability: ${rulePoint.vulnerability.toFixed(2)}</p>` : ''}
        </div>
      `;
    } else if (riskPoint && layers.risk) {
      const riskColor = getRiskColor(riskPoint.risk);
      popupContent += `
        <div class="mb-2">
          <span class="text-xs font-medium">Risk Level:</span>
          <span style="color: ${riskColor}" class="ml-1 font-bold">${(riskPoint.risk * 100).toFixed(0)}%</span>
          <span class="text-xs ml-1 px-1 py-0.5 rounded" style="background-color: ${riskColor}20">${riskPoint.thresholdBand}</span>
        </div>
        <p class="text-xs text-gray-600">ETA: ${riskPoint.etaHours}h</p>
      `;
    }

    popupContent += `</div>`;
    layer.bindPopup(popupContent);
  };

  // Calculate polygon centroid
  const getPolygonCentroid = (coordinates: number[][][]): [number, number] => {
    const coords = coordinates[0]; // Exterior ring
    const latSum = coords.reduce((sum, coord) => sum + coord[1], 0);
    const lngSum = coords.reduce((sum, coord) => sum + coord[0], 0);
    return [latSum / coords.length, lngSum / coords.length];
  };

  // Create critical asset markers
  const createAssetMarkers = () => {
    if (!layers.assets) return null;

    const markers: JSX.Element[] = [];

    zones.features.forEach((feature) => {
      const zone = feature.properties;
      const zoneId = feature.properties.id;

      // Validate geometry and get centroid for marker placement
      if (!feature.geometry?.coordinates || feature.geometry.coordinates[0].length === 0) {
        console.warn(`Invalid coordinates for zone ${zoneId}`);
        return;
      }

      const [centerLat, centerLng] = getPolygonCentroid(feature.geometry.coordinates);

      zone.critical_assets.forEach((asset: string, index: number) => {
        // Slightly offset multiple assets in the same zone for visibility
        const offsetLat = centerLat + (index * 0.002);
        const offsetLng = centerLng + (index * 0.002);

        markers.push(
          <Marker key={`${zoneId}-asset-${index}`} position={[offsetLat, offsetLng]}>
            <Popup>
              <div className="p-2">
                <h4 className="font-semibold text-sm mb-1">{asset}</h4>
                <p className="text-xs text-gray-600">Zone: {zone.name}</p>
                <Badge variant="secondary" className="text-xs">Critical Asset</Badge>
              </div>
            </Popup>
          </Marker>
        );
      });
    });

    return markers;
  };

  return (
    <div className={className}>
      <Card className="overflow-hidden">
        <div className="h-[600px] relative">
          <MapContainer
            center={mapCenter}
            zoom={mapZoom}
            className="h-full w-full"
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MapController
              onZoneSelect={onZoneSelect}
              selectedZone={selectedZone}
              zones={zones}
            />

            {/* GeoJSON zones layer */}
            {layers.zones && (
              <GeoJSON
                data={zones as any}
                style={getZoneStyle}
                onEachFeature={handleZoneClick}
                eventHandlers={{
                  add: (e) => {
                    // Ensure proper layer ordering when zones are added
                    console.log('GeoJSON layer added successfully');
                  },
                  error: (e) => {
                    console.error('GeoJSON layer error:', e);
                  }
                }}
              />
            )}

            {/* Critical asset markers */}
            {createAssetMarkers()}
          </MapContainer>

          {/* Map controls overlay */}
          <div className="absolute top-4 right-4 space-y-2">
            <Card className="p-3 shadow-lg">
              <div className="flex items-center space-x-2 text-xs">
                <Clock className="h-4 w-4" />
                <span className="font-medium">Forecast:</span>
                <Badge variant="outline">{timeHorizon}</Badge>
              </div>
            </Card>

            <Card className="p-3 shadow-lg">
              <div className="flex items-center space-x-2 text-xs">
                <Layers className="h-4 w-4" />
                <span className="font-medium">Layers:</span>
              </div>
              <div className="mt-2 space-y-1 text-xs">
                <div className="flex items-center space-x-1">
                  <div className={`w-3 h-3 rounded ${layers.zones ? 'bg-blue-500' : 'bg-gray-300'}`} />
                  <span>Zones</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className={`w-3 h-3 rounded ${layers.rule ? 'bg-amber-600' : 'bg-gray-300'}`} />
                  <span>Rule-based</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className={`w-3 h-3 rounded ${layers.risk ? 'bg-red-500' : 'bg-gray-300'}`} />
                  <span>Risk</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className={`w-3 h-3 rounded ${layers.assets ? 'bg-purple-500' : 'bg-gray-300'}`} />
                  <span>Assets</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Legends */}
          {(layers.rule || layers.risk) && (
            <div className="absolute bottom-4 left-4 space-y-3">
              {layers.rule && (
                <Card className="p-3 shadow-lg">
                  <div className="text-xs font-medium mb-2">Rule-based categories</div>
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: getRuleColor('CRITICAL') }} />
                      <span>Critical</span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: getRuleColor('WARNING') }} />
                      <span>Warning</span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: getRuleColor('ADVISORY') }} />
                      <span>Advisory</span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: getRuleColor('NORMAL') }} />
                      <span>Normal</span>
                    </div>
                  </div>
                </Card>
              )}

              {layers.risk && (
                <Card className="p-3 shadow-lg">
                  <div className="text-xs font-medium mb-2">Risk Levels</div>
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }} />
                      <span>Severe (&gt;75%)</span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f97316' }} />
                      <span>High (50-75%)</span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: '#eab308' }} />
                      <span>Moderate (25-50%)</span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: '#22c55e' }} />
                      <span>Low (&lt;25%)</span>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
