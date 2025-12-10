import React from 'react';
import { Activity, MapPin, Shield } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useZones, useRiskData } from '@/hooks/useApiData';
import { useSimulatedTimeline } from '@/hooks/useSimulatedTimeline';
import { useAppContext } from '@/contexts/AppContext';

export function CoordinatorZonesPanel() {
  const { timeHorizon } = useAppContext();
  const { timestamp } = useSimulatedTimeline();
  const { data: zones, isLoading: zonesLoading } = useZones();
  const { data: riskData, isLoading: riskLoading } = useRiskData(timestamp, timeHorizon);

  if (zonesLoading || riskLoading || !zones || !riskData) {
    return (
      <Card>
        <CardContent className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
          <Activity className="h-4 w-4 animate-spin" />
          Loading zones…
        </CardContent>
      </Card>
    );
  }

  const zoneRows = zones.features.map(feature => {
    const risk = riskData.find(r => r.zoneId === feature.properties.id);
    return {
      id: feature.properties.id,
      name: feature.properties.name,
      population: feature.properties.population,
      risk: risk?.risk ?? 0,
      band: risk?.thresholdBand ?? 'Low',
      eta: risk?.etaHours ?? 0,
      criticalAssets: feature.properties.critical_assets.length,
    };
  }).sort((a, b) => b.risk - a.risk);

  const bandBadge = (band: string) => {
    const base = band.toLowerCase();
    if (base === 'severe') return <Badge variant="destructive">Severe</Badge>;
    if (base === 'high') return <Badge variant="default">High</Badge>;
    if (base === 'moderate') return <Badge variant="secondary">Moderate</Badge>;
    return <Badge variant="outline">Low</Badge>;
  };

  return (
    <Card>
      <CardHeader className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <MapPin className="h-4 w-4 text-sky-600" />
            Zones at a glance
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Sorted by current simulated risk ({timeHorizon} horizon)
          </p>
        </div>
        <Badge variant="outline" className="flex items-center gap-1">
          <Shield className="h-3 w-3" />
          {zoneRows.filter(z => z.risk >= 0.5).length} high-risk zones
        </Badge>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-muted-foreground">
            <tr className="border-b">
              <th className="py-2 pr-4">Zone</th>
              <th className="py-2 pr-4">Population</th>
              <th className="py-2 pr-4">Risk</th>
              <th className="py-2 pr-4">ETA</th>
              <th className="py-2 pr-4">Critical assets</th>
            </tr>
          </thead>
          <tbody>
            {zoneRows.map(zone => (
              <tr key={zone.id} className="border-b last:border-0">
                <td className="py-2 pr-4 font-medium">{zone.name}</td>
                <td className="py-2 pr-4 text-muted-foreground">{zone.population.toLocaleString()}</td>
                <td className="py-2 pr-4">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-20 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-sky-600"
                        style={{ width: `${Math.min(100, Math.round(zone.risk * 100))}%` }}
                      />
                    </div>
                    <span className="font-semibold">{Math.round(zone.risk * 100)}%</span>
                    {bandBadge(zone.band)}
                  </div>
                </td>
                <td className="py-2 pr-4 text-muted-foreground">{zone.eta} h</td>
                <td className="py-2 pr-4 text-muted-foreground">{zone.criticalAssets}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
