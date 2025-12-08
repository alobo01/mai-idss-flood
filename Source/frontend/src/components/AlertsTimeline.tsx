import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAlerts } from '@/hooks/useApiData';
import type { Alert, AlertSeverity } from '@/types';
import { AlertItem } from './alerts/AlertItem';
import { AlertFilter } from './alerts/AlertFilter';

interface AlertsTimelineProps {
  className?: string;
  selectedZone?: string | null;
  maxHeight?: string;
}

export function AlertsTimeline({ className, selectedZone, maxHeight = '600px' }: AlertsTimelineProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const { data: alerts = [], isLoading, error } = useAlerts();

  // Filter alerts based on selected zone and severity
  const filteredAlerts = alerts.filter((alert: Alert) => {
    const matchesZone = !selectedZone || alert.zoneId === selectedZone;
    const matchesSeverity = selectedSeverity === 'all' || alert.severity === selectedSeverity;
    return matchesZone && matchesSeverity;
  });

  const handleAcknowledged = () => {
    // Refresh will be handled by the AlertItem component
  };

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Error loading alerts</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Alerts
          <span className="text-sm font-normal text-muted-foreground">
            {filteredAlerts.length} active
          </span>
        </CardTitle>

        <AlertFilter
          selectedSeverity={selectedSeverity}
          onSeverityChange={setSelectedSeverity}
          onFilterToggle={() => setIsFilterOpen(!isFilterOpen)}
          isFilterOpen={isFilterOpen}
        />
      </CardHeader>

      <CardContent className="p-0">
        <ScrollArea style={{ height: maxHeight }}>
          {isLoading ? (
            <div className="p-4">
              <p className="text-muted-foreground">Loading alerts...</p>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="p-4">
              <p className="text-muted-foreground text-center">
                {selectedZone || selectedSeverity !== 'all'
                  ? 'No alerts match the current filters'
                  : 'No active alerts'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredAlerts.map((alert: Alert) => (
                <AlertItem
                  key={alert.id}
                  alert={alert}
                  onAcknowledged={handleAcknowledged}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}