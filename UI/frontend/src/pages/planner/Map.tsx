import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, TrendingUp, Clock } from 'lucide-react';
import { MapView } from '@/components/MapView';
import { StLouisFloodPanel } from '@/components/StLouisFloodPanel';
import { HistoricalDataPanel } from '@/components/HistoricalDataPanel';
import { useAppContext } from '@/contexts/AppContext';
import { useSimulatedTimeline } from '@/hooks/useSimulatedTimeline';
import { useRuleBasedPipeline } from '@/hooks/useRuleBased';
import { mockRiskData } from '@/lib/mockData';
import { useZones } from '@/hooks/useZones';
import type { TimeHorizon } from '@/types';

export function PlannerMap() {
  const { selectedZone, setSelectedZone, timeHorizon, setTimeHorizon } = useAppContext();
  const { timestamp: simulatedTimestamp, label: simulatedLabel, speedLabel } = useSimulatedTimeline();
  const [layers, setLayers] = useState({
    zones: true,
    risk: false, // Hide traditional risk layer to reduce clutter
    rule: true,  // Show only rule-based categories as "risk level"
    gauges: true,
    alerts: true,
  });
  const { zones, zonesGeo, gauges } = useZones();

  const { leadTimeDays } = useAppContext();

  // Get fuzzy logic derived states
  const { data: rulePipeline } = useRuleBasedPipeline({
    totalUnits: 12,
    mode: 'fuzzy', // Always use fuzzy logic derived states
    maxUnitsPerZone: 6,
    leadTime: leadTimeDays,
  });

  const handleLayerToggle = (layer: keyof typeof layers) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }));
  };

  const handleTimeHorizonChange = (horizon: TimeHorizon) => {
    setTimeHorizon(horizon);
  };

  const handleZoneSelect = (zoneId: string) => {
    setSelectedZone(zoneId);
  };

  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Planner Risk Map</h1>
          <p className="text-muted-foreground">
            Interactive flood risk assessment and scenario planning
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>{timeHorizon === '1d' ? '1 Day' : timeHorizon === '2d' ? '2 Days' : '3 Days'} forecast</span>
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Forecast:</span>
            {(['1d', '2d', '3d'] as TimeHorizon[]).map((horizon) => (
              <button
                key={horizon}
                onClick={() => handleTimeHorizonChange(horizon)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  timeHorizon === horizon
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {horizon === '1d' ? '1 Day' : horizon === '2d' ? '2 Days' : '3 Days'}
              </button>
            ))}
          </div>
          </div>
      </div>

      <Tabs defaultValue="map" className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <TabsList>
            <TabsTrigger value="map">Risk Map</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
            {/* Scenarios feature not implemented yet - removed */}
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{simulatedLabel}</span>
            <Badge variant="outline">{speedLabel}</Badge>
          </div>
        </div>

        <TabsContent value="map" className="space-y-4">
          <MapView
            zones={zonesGeo || { type: 'FeatureCollection', features: [] } as any}
            gauges={gauges}
            riskData={mockRiskData}
            ruleData={rulePipeline?.allocations || []}
            selectedZone={selectedZone}
            onZoneSelect={handleZoneSelect}
            timeHorizon={timeHorizon}
            layers={layers}
          />

          {/* St. Louis Dashboard - placed under the map */}
          <StLouisFloodPanel />
        </TabsContent>

        <TabsContent value="analysis">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5" />
                <span>Risk Analysis Dashboard</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Risk Summary Cards */}
                <>
                  <Card className="p-4">
                    <h4 className="font-medium text-sm text-muted-foreground mb-2">High Risk Zones</h4>
                    <p className="text-2xl font-bold text-red-600">
                      {mockRiskData.filter(r => r.thresholdBand === 'Severe').length}
                    </p>
                  </Card>
                  <Card className="p-4">
                    <h4 className="font-medium text-sm text-muted-foreground mb-2">Average Risk</h4>
                    <p className="text-2xl font-bold">
                      {(mockRiskData.reduce((sum, r) => sum + r.risk, 0) / mockRiskData.length * 100).toFixed(1)}%
                    </p>
                  </Card>
                  <Card className="p-4">
                    <h4 className="font-medium text-sm text-muted-foreground mb-2">Total Population at Risk</h4>
                    <p className="text-2xl font-bold">
                      {mockRiskData
                        .filter(r => r.risk > 0.5)
                        .reduce((sum, r) => {
                          const zone = zones.find(z => z.zone_id === r.zoneId);
                          return sum + (zone ? Math.round(zone.pop_density * 1000) : 0);
                        }, 0)
                        .toLocaleString()}
                    </p>
                  </Card>
                  <Card className="p-4">
                    <h4 className="font-medium text-sm text-muted-foreground mb-2">Critical Assets Threatened</h4>
                    <p className="text-2xl font-bold">
                      {mockRiskData
                        .filter(r => r.risk > 0.5)
                        .reduce((sum, r) => {
                          const zone = zones.find(z => z.zone_id === r.zoneId);
                          return sum + (zone?.critical_infra ? 1 : 0);
                        }, 0)}
                    </p>
                  </Card>
                </>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scenarios tab removed — feature not implemented */}

        <TabsContent value="history">
          <HistoricalDataPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
