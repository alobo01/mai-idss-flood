import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertTriangle,
  Clock,
  MapPin,
  CheckCircle,
  XCircle,
  User,
  Filter,
  Bell,
  BellOff
} from 'lucide-react';
import { useAlerts, useAcknowledgeAlert } from '@/hooks/useApiData';
import type { Alert, AlertSeverity, AlertStatus } from '@/types';
import { format } from 'date-fns';
import { useQueryClient } from '@tanstack/react-query';

interface AlertsTimelineProps {
  className?: string;
  selectedZone?: string | null;
  maxHeight?: string;
}

const severityColors: Record<AlertSeverity, string> = {
  Low: 'bg-blue-100 text-blue-800 border-blue-200',
  Moderate: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  High: 'bg-orange-100 text-orange-800 border-orange-200',
  Severe: 'bg-red-100 text-red-800 border-red-200',
  Operational: 'bg-gray-100 text-gray-800 border-gray-200',
};

const statusIcons: Record<AlertStatus, React.ReactNode> = {
  open: <XCircle className="h-4 w-4 text-red-500" />,
  acknowledged: <Clock className="h-4 w-4 text-yellow-500" />,
  resolved: <CheckCircle className="h-4 w-4 text-green-500" />,
};

const severityIcons: Record<AlertSeverity, React.ReactNode> = {
  Low: <AlertTriangle className="h-4 w-4 text-blue-500" />,
  Moderate: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
  High: <AlertTriangle className="h-4 w-4 text-orange-500" />,
  Severe: <AlertTriangle className="h-4 w-4 text-red-500" />,
  Operational: <AlertTriangle className="h-4 w-4 text-gray-500" />,
};

export function AlertsTimeline({
  className = '',
  selectedZone = null,
  maxHeight = '600px'
}: AlertsTimelineProps) {
  const [filter, setFilter] = useState<{
    severity?: AlertSeverity;
    status?: AlertStatus;
    type?: string;
  }>({});

  const [showMuted, setShowMuted] = useState(true);

  const { data: alerts = [], isLoading, error } = useAlerts();
  const { acknowledgeAlert } = useAcknowledgeAlert();
  const queryClient = useQueryClient();

  // Filter alerts based on props and filters
  const filteredAlerts = alerts.filter(alert => {
    // Zone filter
    if (selectedZone && alert.zoneId !== selectedZone) {
      return false;
    }

    // Severity filter
    if (filter.severity && alert.severity !== filter.severity) {
      return false;
    }

    // Status filter
    if (filter.status && alert.status !== filter.status) {
      return false;
    }

    // Type filter
    if (filter.type && alert.type !== filter.type) {
      return false;
    }

    // Show muted alerts (resolved/closed)
    if (!showMuted && alert.status === 'resolved') {
      return false;
    }

    return true;
  });

  // Sort alerts by timestamp (newest first)
  const sortedAlerts = [...filteredAlerts].sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId);
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getAlertLocation = (alert: Alert) => {
    const zoneMap: Record<string, string> = {
      'Z-ALFA': 'Riverside North',
      'Z-BRAVO': 'Industrial District',
      'Z-CHARLIE': 'Residential Heights',
      'Z-DELTA': 'Commercial Zone',
      'Z-ECHO': 'Riverside South',
    };
    return zoneMap[alert.zoneId] || alert.zoneId;
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bell className="h-5 w-5" />
            <span>Alerts Timeline</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <Clock className="h-6 w-6 animate-spin mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Loading alerts...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bell className="h-5 w-5" />
            <span>Alerts Timeline</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-red-600 py-4">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            <p>Error loading alerts. Please try again.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Bell className="h-5 w-5" />
            <span>Alerts Timeline</span>
            <Badge variant="secondary" className="ml-2">
              {sortedAlerts.filter(a => a.status === 'open').length} active
            </Badge>
          </CardTitle>

          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowMuted(!showMuted)}
              className="h-8 w-8 p-0"
            >
              {showMuted ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
            </Button>

            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <Filter className="h-4 w-4" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Filter Alerts</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Severity</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {Object.keys(severityColors).map((severity) => (
                        <Button
                          key={severity}
                          variant={filter.severity === severity ? 'default' : 'outline'}
                          size="sm"
                          onClick={() =>
                            setFilter(prev => ({
                              ...prev,
                              severity: prev.severity === severity ? undefined : severity as AlertSeverity
                            }))
                          }
                        >
                          {severity}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium">Status</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {(['open', 'acknowledged', 'resolved'] as AlertStatus[]).map((status) => (
                        <Button
                          key={status}
                          variant={filter.status === status ? 'default' : 'outline'}
                          size="sm"
                          onClick={() =>
                            setFilter(prev => ({
                              ...prev,
                              status: prev.status === status ? undefined : status
                            }))
                          }
                        >
                          {status}
                        </Button>
                      ))}
                    </div>
                  </div>

                  {(Object.keys(filter).length > 0) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setFilter({})}
                      className="w-full"
                    >
                      Clear Filters
                    </Button>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <ScrollArea className="pr-4" style={{ maxHeight }}>
          {sortedAlerts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No alerts found</p>
              {selectedZone && (
                <p className="text-sm mt-1">No alerts for {getAlertLocation({ zoneId: selectedZone } as Alert)}</p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {sortedAlerts.map((alert) => (
                <AlertItem
                  key={alert.id}
                  alert={alert}
                  onAcknowledge={handleAcknowledgeAlert}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Individual Alert Item Component
function AlertItem({
  alert,
  onAcknowledge,
}: {
  alert: Alert;
  onAcknowledge: (id: string) => void;
}) {
  const getAlertLocation = (alert: Alert) => {
    const zoneMap: Record<string, string> = {
      'Z-ALFA': 'Riverside North',
      'Z-BRAVO': 'Industrial District',
      'Z-CHARLIE': 'Residential Heights',
      'Z-DELTA': 'Commercial Zone',
      'Z-ECHO': 'Riverside South',
    };
    return zoneMap[alert.zoneId] || alert.zoneId;
  };

  return (
    <div className={`relative pl-6 pb-4 border-l-2 ${
      alert.status === 'resolved' ? 'border-gray-300' :
      alert.severity === 'Severe' ? 'border-red-500' :
      alert.severity === 'High' ? 'border-orange-500' :
      alert.severity === 'Moderate' ? 'border-yellow-500' :
      'border-blue-500'
    }`}>
      {/* Timeline dot */}
      <div className={`absolute -left-2 top-2 w-4 h-4 rounded-full border-2 bg-white ${
        alert.status === 'resolved' ? 'border-gray-300' :
        alert.severity === 'Severe' ? 'border-red-500' :
        alert.severity === 'High' ? 'border-orange-500' :
        alert.severity === 'Moderate' ? 'border-yellow-500' :
        'border-blue-500'
      }`}>
        <div className={`w-2 h-2 rounded-full mx-auto mt-0.5 ${
          alert.status === 'resolved' ? 'bg-gray-300' :
          alert.severity === 'Severe' ? 'bg-red-500' :
          alert.severity === 'High' ? 'bg-orange-500' :
          alert.severity === 'Moderate' ? 'bg-yellow-500' :
          'bg-blue-500'
        }`} />
      </div>

      {/* Alert content */}
      <div className={`rounded-lg border p-3 ${
        alert.status === 'resolved' ? 'bg-gray-50 border-gray-200' :
        alert.severity === 'Severe' ? 'bg-red-50 border-red-200' :
        alert.severity === 'High' ? 'bg-orange-50 border-orange-200' :
        alert.severity === 'Moderate' ? 'bg-yellow-50 border-yellow-200' :
        'bg-blue-50 border-blue-200'
      }`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              {severityIcons[alert.severity]}
              <h4 className="font-medium text-sm">{alert.title}</h4>
              <Badge
                variant={alert.severity === 'Severe' ? 'destructive' : 'secondary'}
                className="text-xs"
              >
                {alert.severity}
              </Badge>
              <Badge
                variant="outline"
                className="text-xs"
              >
                {alert.type}
              </Badge>
            </div>

            <p className="text-sm text-muted-foreground mb-2">{alert.description}</p>

            <div className="flex items-center space-x-4 text-xs text-muted-foreground">
              <div className="flex items-center space-x-1">
                <MapPin className="h-3 w-3" />
                <span>{getAlertLocation(alert)}</span>
              </div>

              {alert.eta && (
                <div className="flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>ETA: {alert.eta}</span>
                </div>
              )}

              {alert.crewId && (
                <div className="flex items-center space-x-1">
                  <User className="h-3 w-3" />
                  <span>{alert.crewId}</span>
                </div>
              )}

              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{format(new Date(alert.timestamp), 'MMM d, HH:mm')}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-1 ml-2">
            {statusIcons[alert.status]}
            {alert.status === 'open' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onAcknowledge(alert.id)}
                className="h-6 px-2 text-xs"
              >
                Acknowledge
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}