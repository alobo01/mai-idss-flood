
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, TrendingUp, MapPin, Clock } from 'lucide-react';
import { MapView } from '@/components/MapView';
import { useZones, useRiskData, useAlerts } from '@/hooks/useApiData';
import { useAppContext } from '@/contexts/AppContext';
import { useSimulatedTimeline } from '@/hooks/useSimulatedTimeline';
import type { TimeHorizon } from '@/types';
import { StLouisFloodPanel } from '@/components/StLouisFloodPanel';
import { useRuleBasedPipeline } from '@/hooks/useRuleBased';

export function PlannerMap() {
  const { selectedZone, setSelectedZone, timeHorizon, setTimeHorizon } = useAppContext();
  const { timestamp: simulatedTimestamp, label: simulatedLabel, speedLabel } = useSimulatedTimeline();
  const [layers, setLayers] = useState({
    zones: true,
    risk: true,
    rule: true,
    assets: true,
    gauges: true,
    alerts: true,
  });

  // Fetch data from API
  const { data: zones, isLoading: zonesLoading, error: zonesError } = useZones();
  const { data: riskData, isLoading: riskLoading, error: riskError } = useRiskData(simulatedTimestamp, timeHorizon);
  const { data: alerts, isLoading: alertsLoading, error: alertsError } = useAlerts();
  const { data: rulePipeline, isLoading: ruleLoading, error: ruleError } = useRuleBasedPipeline({
    globalPf: 0.55,
    totalUnits: 12,
    mode: 'crisp',
    maxUnitsPerZone: 6,
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

  const selectedZoneData = zones?.features.find(zone => zone.properties.id === selectedZone);
  const selectedRiskData = riskData?.find(risk => risk.zoneId === selectedZone);
  const selectedRuleData = rulePipeline?.allocations?.find(allocation => allocation.zone_id === selectedZone);
  const selectedZoneAlerts = alerts?.filter(alert => alert.zoneId === selectedZone);
  const isLoading = zonesLoading || riskLoading || alertsLoading || ruleLoading;
  const hasError = Boolean(zonesError || riskError || alertsError || ruleError);

  const renderContent = () => {
    if (hasError) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center text-red-600">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            <p>Error loading map data. Please try again.</p>
          </div>
        </div>
      );
    }

    if (!zones || !riskData || !alerts || isLoading) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Clock className="h-8 w-8 animate-spin mx-auto mb-2" />
            <p>Loading map data...</p>
          </div>
        </div>
      );
    }

    return (
      <Tabs defaultValue="map" className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <TabsList>
            <TabsTrigger value="map">Risk Map</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
            <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          </TabsList>
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{simulatedLabel}</span>
            <Badge variant="outline">{speedLabel}</Badge>
          </div>
        </div>

        <TabsContent value="map" className="space-y-4">
          <MapView
            zones={zones}
            riskData={riskData}
            ruleData={rulePipeline?.allocations || []}
            selectedZone={selectedZone}
            onZoneSelect={handleZoneSelect}
            timeHorizon={timeHorizon}
            layers={layers}
          />

          {/* Zone Details Panel */}
          {selectedZoneData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MapPin className="h-5 w-5" />
                  <span>{selectedZoneData.properties.name}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  <div>
                    <h4 className="font-medium mb-2">Zone Information</h4>
                    <dl className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-muted-foreground">Population:</dt>
                        <dd>{selectedZoneData.properties.population.toLocaleString()}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-muted-foreground">Critical Assets:</dt>
                        <dd>{selectedZoneData.properties.critical_assets.length}</dd>
                      </div>
                    </dl>
                  </div>

                  {selectedRiskData && (
                    <div>
                      <h4 className="font-medium mb-2">Risk Assessment</h4>
                      <dl className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-muted-foreground">Risk Level:</dt>
                          <dd className="font-medium">
                            {(selectedRiskData.risk * 100).toFixed(0)}%
                          </dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-muted-foreground">Category:</dt>
                          <dd>
                            <Badge
                              variant={
                                selectedRiskData.thresholdBand === 'Severe' ? 'destructive' :
                                selectedRiskData.thresholdBand === 'High' ? 'default' :
                                selectedRiskData.thresholdBand === 'Moderate' ? 'secondary' : 'outline'
                              }
                            >
                              {selectedRiskData.thresholdBand}
                            </Badge>
                          </dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-muted-foreground">ETA:</dt>
                          <dd>{selectedRiskData.etaHours} hours</dd>
                        </div>
                      </dl>
                    </div>
                  )}

                  {selectedRuleData && (
                    <div>
                      <h4 className="font-medium mb-2">Rule-based response</h4>
                      <dl className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-muted-foreground">Impact:</dt>
                          <dd>
                            <Badge variant="outline" className="text-xs">
                              {(selectedRuleData.impact_level || '').toUpperCase()}
                            </Badge>
                          </dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-muted-foreground">Units allocated:</dt>
                          <dd className="font-medium">{selectedRuleData.units_allocated}</dd>
                        </div>
                        {selectedRuleData.pf !== undefined && (
                          <div className="flex justify-between">
                            <dt className="text-muted-foreground">PF:</dt>
                            <dd>{(selectedRuleData.pf * 100).toFixed(0)}%</dd>
                          </div>
                        )}
                        {selectedRuleData.vulnerability !== undefined && (
                          <div className="flex justify-between">
                            <dt className="text-muted-foreground">Vulnerability:</dt>
                            <dd>{selectedRuleData.vulnerability.toFixed(2)}</dd>
                          </div>
                        )}
                      </dl>
                    </div>
                  )}

                  <div>
                    <h4 className="font-medium mb-2">Active Alerts</h4>
                    <div className="space-y-1">
                      {selectedZoneAlerts && selectedZoneAlerts.length > 0 ? (
                        selectedZoneAlerts.slice(0, 3).map(alert => (
                          <div key={alert.id} className="text-xs p-2 bg-muted rounded">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{alert.title}</span>
                              <Badge
                                variant={alert.severity === 'Severe' ? 'destructive' : 'secondary'}
                                className="text-xs"
                              >
                                {alert.severity}
                              </Badge>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-muted-foreground">No active alerts</p>
                      )}
                    </div>
                  </div>
                </div>

                {selectedZoneData.properties.critical_assets.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">Critical Assets</h4>
                    <div className="flex flex-wrap gap-1">
                      {selectedZoneData.properties.critical_assets.map((asset, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {asset}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
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
                {riskData && zones && (
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
                        {(riskData.reduce((sum, r) => sum + r.risk, 0) / riskData.length * 100).toFixed(1)}%
                      </p>
                    </Card>
                    <Card className="p-4">
                      <h4 className="font-medium text-sm text-muted-foreground mb-2">Total Population at Risk</h4>
                      <p className="text-2xl font-bold">
                        {riskData
                          .filter(r => r.risk > 0.5)
                          .reduce((sum, r) => {
                            const zone = zones.features.find(z => z.properties.id === r.zoneId);
                            return sum + (zone?.properties.population || 0);
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
                            const zone = zones.features.find(z => z.properties.id === r.zoneId);
                            return sum + (zone?.properties.critical_assets.length || 0);
                          }, 0)}
                      </p>
                    </Card>
                  </>
                )}
              </div>

              {/* Risk Drivers Analysis */}
              <div className="mt-6">
                <h4 className="font-medium mb-4">Risk Drivers Analysis</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {riskData?.slice(0, 3).map(risk => {
                    const zone = zones?.features.find(z => z.properties.id === risk.zoneId);
                    return (
                      <Card key={risk.zoneId} className="p-4">
                        <h5 className="font-medium mb-2">{zone?.properties.name}</h5>
                        <div className="space-y-2">
                          {risk.drivers.slice(0, 3).map((driver, index) => (
                            <div key={index} className="flex justify-between text-sm">
                              <span className="text-muted-foreground">{driver.feature}:</span>
                              <span className="font-medium">{(driver.contribution * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scenarios">
          <Card>
            <CardHeader>
              <CardTitle>Scenario Planning</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <TrendingUp className="h-12 w-12 mx-auto mb-4" />
                <p>Scenario planning tools will be implemented here</p>
                <p className="text-sm mt-2">
                  This will include "what-if" analysis, mitigation scenarios, and resource allocation planning
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    );
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
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="flex items-center space-x-1">
            <Clock className="h-3 w-3" />
            <span>{timeHorizon} forecast</span>
          </Badge>
          {selectedZone && (
            <Badge variant="secondary" className="flex items-center space-x-1">
              <MapPin className="h-3 w-3" />
              <span>{selectedZoneData?.properties.name}</span>
            </Badge>
          )}
        </div>
      </div>

      <StLouisFloodPanel />

      {renderContent()}
    </div>
  );
}
