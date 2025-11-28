import React from 'react';
import { MapView } from '@/components/MapView';
import { useZones, useRiskData } from '@/hooks/useApiData';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, MapPin } from 'lucide-react';

export function MapTestPage() {
  const { data: zones, isLoading: zonesLoading, error: zonesError } = useZones();
  const { data: riskData, isLoading: riskLoading, error: riskError } = useRiskData();

  if (zonesLoading || riskLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/3 mb-4"></div>
          <div className="h-[600px] bg-gray-300 rounded"></div>
        </div>
      </div>
    );
  }

  if (zonesError || riskError || !zones) {
    return (
      <div className="p-8">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Map Loading Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p><strong>Zones Error:</strong> {zonesError?.message || 'None'}</p>
              <p><strong>Risk Error:</strong> {riskError?.message || 'None'}</p>
              <p><strong>Zones Data:</strong> {zones ? 'Available' : 'Not available'}</p>
              <p><strong>Risk Data:</strong> {riskData ? 'Available' : 'Not available'}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <MapPin className="h-8 w-8" />
          Leaflet Map Test
        </h1>
        <p className="text-gray-600 mt-2">
          Testing the Leaflet implementation with real GeoJSON zone data
        </p>
      </div>

      <div className="grid gap-6">
        <MapView
          zones={zones}
          riskData={riskData || []}
          layers={{
            zones: true,
            risk: true,
            assets: true,
            gauges: true
          }}
          timeHorizon="12h"
          onZoneSelect={(zoneId) => {
            console.log('Selected zone:', zoneId);
          }}
        />

        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Zone Data</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <p><strong>Total Zones:</strong> {zones.features.length}</p>
                <p><strong>Available:</strong> Yes</p>
                <p><strong>Geometry Type:</strong> {zones.features[0]?.geometry?.type}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Risk Data</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <p><strong>Risk Points:</strong> {riskData?.length || 0}</p>
                <p><strong>Available:</strong> {riskData ? 'Yes' : 'No'}</p>
                <p><strong>Time Horizon:</strong> 12h forecast</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}