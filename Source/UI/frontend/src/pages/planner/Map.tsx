import React, { useMemo, useState } from 'react';
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
import { useZones } from '@/hooks/useZones';
import type { TimeHorizon, RuleScenario, RiskPoint } from '@/types';
import { RULE_SCENARIO_LABELS } from '@/types';

interface PlannerMapProps {
  selectedDate?: string;
}

export function PlannerMap({ selectedDate }: PlannerMapProps) {
  const {
    selectedZone,
    setSelectedZone,
    timeHorizon,
    setTimeHorizon,
    leadTimeDays,
    scenario,
    setScenario,
  } = useAppContext();
  const { timestamp: simulatedTimestamp, label: simulatedLabel } = useSimulatedTimeline();
  const [layers, setLayers] = useState({
    zones: true,
    risk: false, // Hide traditional risk layer to reduce clutter
    rule: true,  // Show only rule-based categories as "risk level"
    gauges: true,
    alerts: true,
  });
  const { zones, zonesGeo, gauges } = useZones();

  const mapGauges = useMemo(() => {
    // Hide St. Louis gauge on the map (USGS 07010000 / id "target")
    return (gauges || []).filter((g) => g.id !== 'target' && g.usgs_id !== '07010000');
  }, [gauges]);

  // Get fuzzy logic derived states
  const { data: rulePipeline } = useRuleBasedPipeline({
    totalUnits: 12,
    mode: 'fuzzy', // Always use fuzzy logic derived states
    maxUnitsPerZone: 6,
    leadTime: leadTimeDays,
    scenario,
    asOfDate: selectedDate,
  });

  const selectedLevel = rulePipeline?.lastPrediction?.selected_level;
  const selectedLevelSource = rulePipeline?.lastPrediction?.selected_level_source;
  const piLower = rulePipeline?.lastPrediction?.lower_bound_80;
  const piUpper = rulePipeline?.lastPrediction?.upper_bound_80;
  const selectedProbability = rulePipeline?.globalProbability;

  const formatLevelValue = (value?: number | null) =>
    value != null && Number.isFinite(value) ? `${value.toFixed(2)} ft` : '—';

  const formatProbabilityValue = (value?: number | null) =>
    value != null && Number.isFinite(value)
      ? `${(value * 100).toFixed(0)}%`
      : '—';

  const formatPiRange = (lower?: number | null, upper?: number | null) =>
    lower != null && upper != null && Number.isFinite(lower) && Number.isFinite(upper)
      ? `${lower.toFixed(2)} – ${upper.toFixed(2)} ft`
      : '—';

  const levelSourceLabel = (() => {
    switch (selectedLevelSource) {
      case 'prediction_interval_lower':
        return 'PI lower';
      case 'prediction_interval_upper':
        return 'PI upper';
      case 'median':
        return 'Median';
      case 'fallback':
        return 'Fallback';
      default:
        return 'Selected';
    }
  })();

  const riskData: RiskPoint[] = useMemo(() => {
    const impactToBand = (impact?: string): RiskPoint['thresholdBand'] => {
      switch ((impact || '').toUpperCase()) {
        case 'CRITICAL':
          return 'Severe';
        case 'WARNING':
          return 'High';
        case 'ADVISORY':
          return 'Moderate';
        default:
          return 'Low';
      }
    };

    const impactToRisk = (impact?: string): number => {
      switch ((impact || '').toUpperCase()) {
        case 'CRITICAL':
          return 0.9;
        case 'WARNING':
          return 0.7;
        case 'ADVISORY':
          return 0.45;
        default:
          return 0.2;
      }
    };

    const etaHours = Math.max(1, leadTimeDays) * 24;
    const allocations = rulePipeline?.allocations || [];

    return allocations.map((a) => ({
      zoneId: a.zone_id,
      risk: a.pf ?? impactToRisk(a.impact_level),
      drivers: [],
      thresholdBand: impactToBand(a.impact_level),
      etaHours,
    }));
  }, [rulePipeline, leadTimeDays]);

  const handleLayerToggle = (layer: keyof typeof layers) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }));
  };

  const handleTimeHorizonChange = (horizon: TimeHorizon) => {
    setTimeHorizon(horizon);
  };

  const handleScenarioChange = (value: RuleScenario) => {
    setScenario(value);
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
        <div className="flex flex-col gap-3">
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>{timeHorizon === '1d' ? '1 Day' : timeHorizon === '2d' ? '2 Days' : '3 Days'} forecast</span>
            </Badge>
          </div>
          <div className="flex flex-wrap items-center gap-2">
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
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium">Scenario:</span>
              {(['best', 'normal', 'worst'] as RuleScenario[]).map((option) => (
                <button
                  key={option}
                  onClick={() => handleScenarioChange(option)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    scenario === option
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {RULE_SCENARIO_LABELS[option]}
                </button>
              ))}
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <div className="flex items-center justify-between">
                <span>Forecast level ({levelSourceLabel}):</span>
                <span className="ml-2 font-semibold text-foreground">{formatLevelValue(selectedLevel)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Interval range:</span>
                <span className="ml-2 font-semibold text-foreground">{formatPiRange(piLower, piUpper)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Flood probability:</span>
                <span className="ml-2 font-semibold text-foreground">{formatProbabilityValue(selectedProbability)}</span>
              </div>
            </div>
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
          </div>
        </div>

        <TabsContent value="map" className="space-y-4">
          <MapView
            zones={zonesGeo || { type: 'FeatureCollection', features: [] } as any}
            gauges={mapGauges}
            riskData={riskData}
            ruleData={rulePipeline?.allocations || []}
            selectedZone={selectedZone}
            onZoneSelect={handleZoneSelect}
            timeHorizon={timeHorizon}
            layers={layers}
            scenario={scenario}
            selectedProbability={selectedProbability}
            selectedLevel={selectedLevel}
            selectedLevelSource={selectedLevelSource}
            piLower={piLower}
            piUpper={piUpper}
          />

          {/* St. Louis Dashboard - placed under the map */}
          <StLouisFloodPanel selectedDate={selectedDate} />
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
                      {riskData.filter(r => r.thresholdBand === 'Severe').length}
                    </p>
                  </Card>
                  <Card className="p-4">
                    <h4 className="font-medium text-sm text-muted-foreground mb-2">Average Risk</h4>
                    <p className="text-2xl font-bold">
                      {riskData.length
                        ? ((riskData.reduce((sum, r) => sum + r.risk, 0) / riskData.length) * 100).toFixed(1)
                        : '—'}
                    </p>
                  </Card>
                  <Card className="p-4">
                    <h4 className="font-medium text-sm text-muted-foreground mb-2">Total Population at Risk</h4>
                    <p className="text-2xl font-bold">
                      {riskData
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
                      {riskData
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
