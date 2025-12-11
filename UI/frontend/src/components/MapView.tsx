import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Layers, Clock, MapPin } from 'lucide-react';
import { PipelineRuleBasedAllocation } from '@/hooks/useRuleBased';
import type {
  GeoJSON as GeoJSONType,
  RiskPoint,
  GaugePoint
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
    gauges: boolean;
  };
  gauges?: GaugePoint[];
  className?: string;
}

// Component to handle map events and bounds
const MapController: React.FC<{
  onZoneSelect?: (zoneId: string) => void;
  selectedZone?: string | null;
  zones: GeoJSONType;
}> = () => {
  const map = useMap();
  const [viewInitialized, setViewInitialized] = useState(false);

  useEffect(() => {
    // Only set view once on initial load to preserve user position during data updates
    if (!viewInitialized) {
      try {
        map.setView([38.627, -90.199], 13);
        setViewInitialized(true);
      } catch (error) {
        console.warn('Could not set map view to St. Louis center:', error);
      }
    }

    const handleClick = () => {
      // This will be handled by GeoJSON layer events
    };

    map.on('click', handleClick);
    return () => {
      map.off('click', handleClick);
    };
  }, [map]);

  return null;
};

export function MapView({
  zones,
  riskData = [],
  ruleData = [],
  selectedZone,
  onZoneSelect,
  layers = { zones: true, risk: true, rule: true, gauges: true },
  gauges = [],
  className = ''
}: MapViewProps) {
  const [mapCenter] = useState<[number, number]>([38.627, -90.199]); // St. Louis
  const [mapZoom] = useState(15);

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

  // Get risk color based on value - high contrast version
  const getRiskColor = (riskValue: number): string => {
    if (riskValue >= 0.75) return '#dc2626'; // red-600 (higher contrast)
    if (riskValue >= 0.5) return '#ea580c'; // orange-600 (higher contrast)
    if (riskValue >= 0.25) return '#ca8a04'; // yellow-600 (higher contrast)
    return '#15803d'; // green-600 (higher contrast)
  };

  // Rule-based impact colors - high contrast version
  const getRuleColor = (impact?: string): string => {
    switch ((impact || '').toUpperCase()) {
      case 'CRITICAL':
        return '#991b1b'; // red-800 (highest contrast)
      case 'WARNING':
        return '#c2410c'; // orange-800 (high contrast)
      case 'ADVISORY':
        return '#a16207'; // yellow-800 (high contrast)
      case 'NORMAL':
        return '#166534'; // green-800 (high contrast)
      default:
        return '#374151'; // gray-700 fallback (better contrast)
    }
  };

  const getZoneId = (feature: any) =>
    feature?.properties?.id || feature?.properties?.zone_id || feature?.properties?.zoneId;

  // Style GeoJSON zones based on risk data
  const getZoneStyle = (feature: any) => {
    const zoneId = getZoneId(feature);
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
    const zoneId = getZoneId(feature);
    if (onZoneSelect) {
      onZoneSelect(zoneId);
    }

    // Bind popup to the layer
    const zoneName = feature.properties.name || feature.properties.zone_id || zoneId;
    const population = feature.properties.population ?? feature.properties.pop_density;
    const zipCode = feature.properties.zip_code || feature.properties.zip || feature.properties.zipCode;
    const rulePoint = ruleData.find(r => r.zone_id === zoneId);
    const riskPoint = riskData.find(r => r.zoneId === zoneId);

    let popupContent = `
      <div class="p-3 min-w-[200px]">
        <h3 class="font-semibold text-sm mb-2">${zoneName}</h3>
        <p class="text-xs text-gray-600 mb-1">Zone ID: ${zoneId}</p>
        ${zipCode ? `<p class="text-xs text-gray-600 mb-2">ZIP Code: ${zipCode}</p>` : ''}
        <p class="text-xs text-gray-600 mb-2">Population: ${population ? Number(population).toLocaleString() : '—'}</p>
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

  // Gauge markers only
  const gaugeMarkers = () => {
    if (!layers.gauges) return null;
    return gauges.map((g) => (
      <Marker key={g.id} position={[g.lat, g.lon]}>
        <Popup>
          <div className="p-2">
            <h4 className="font-semibold text-sm mb-1">{g.name}</h4>
            <p className="text-xs text-gray-600">USGS {g.usgs_id}</p>
            <Badge variant="secondary" className="text-xs">Gauge</Badge>
          </div>
        </Popup>
      </Marker>
    ));
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
                  add: () => {
                    // Ensure proper layer ordering when zones are added
                    console.log('GeoJSON layer added successfully');
                  },
                  error: () => {
                    console.error('GeoJSON layer error');
                  }
                }}
              />
            )}

            {/* Gauges */}
            {gaugeMarkers()}
          </MapContainer>

  
          {/* Risk Level Legend */}
          {layers.rule && (
            <div className="absolute bottom-4 left-4 z-[1000]">
              <Card className="p-4 border-2 border-border shadow-lg bg-card">
                <div className="text-sm font-bold mb-3 text-foreground">Risk Level</div>
                <div className="space-y-2">
                  <div className="status-indicator">
                    <div className="w-5 h-5 rounded border-2 border-red-700" style={{ backgroundColor: getRuleColor('CRITICAL') }} aria-hidden="true" />
                    <span className="font-medium">Critical</span>
                  </div>
                  <div className="status-indicator">
                    <div className="w-5 h-5 rounded border-2 border-orange-700" style={{ backgroundColor: getRuleColor('WARNING') }} aria-hidden="true" />
                    <span className="font-medium">Warning</span>
                  </div>
                  <div className="status-indicator">
                    <div className="w-5 h-5 rounded border-2 border-yellow-700" style={{ backgroundColor: getRuleColor('ADVISORY') }} aria-hidden="true" />
                    <span className="font-medium">Advisory</span>
                  </div>
                  <div className="status-indicator">
                    <div className="w-5 h-5 rounded border-2 border-green-700" style={{ backgroundColor: getRuleColor('NORMAL') }} aria-hidden="true" />
                    <span className="font-medium">Normal</span>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
