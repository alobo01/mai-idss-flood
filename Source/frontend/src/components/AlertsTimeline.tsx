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
  Low: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800',
  Moderate: 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800',
  High: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-800',
  Severe: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800',
  Operational: 'bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-900 dark:text-gray-300 dark:border-gray-700',
};

const statusIcons: Record<AlertStatus, React.ReactNode> = {
  open: <XCircle className="h-4 w-4 text-red-500 dark:text-red-400" />,
  acknowledged: <Clock className="h-4 w-4 text-yellow-500 dark:text-yellow-400" />,
  resolved: <CheckCircle className="h-4 w-4 text-green-500 dark:text-green-400" />,
};

const severityIcons: Record<AlertSeverity, React.ReactNode> = {
  Low: <AlertTriangle className="h-4 w-4 text-blue-500 dark:text-blue-400" />,
  Moderate: <AlertTriangle className="h-4 w-4 text-yellow-500 dark:text-yellow-400" />,
  High: <AlertTriangle className="h-4 w-4 text-orange-500 dark:text-orange-400" />,
  Severe: <AlertTriangle className="h-4 w-4 text-red-500 dark:text-red-400" />,
  Operational: <AlertTriangle className="h-4 w-4 text-gray-500 dark:text-gray-400" />,
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

  const getTimelineColors = () => {
    if (alert.status === 'resolved') {
      return 'border-gray-200 dark:border-gray-600';
    }
    switch (alert.severity) {
      case 'Severe': return 'border-red-500 dark:border-red-400';
      case 'High': return 'border-orange-500 dark:border-orange-400';
      case 'Moderate': return 'border-yellow-500 dark:border-yellow-400';
      case 'Low': return 'border-blue-500 dark:border-blue-400';
      default: return 'border-gray-500 dark:border-gray-400';
    }
  };

  const getDotColors = () => {
    if (alert.status === 'resolved') {
      return {
        border: 'border-gray-300 dark:border-gray-600',
        background: 'bg-white dark:bg-gray-800',
        inner: 'bg-gray-400 dark:bg-gray-500'
      };
    }
    switch (alert.severity) {
      case 'Severe': return {
        border: 'border-red-500 dark:border-red-400',
        background: 'bg-white dark:bg-gray-800',
        inner: 'bg-red-500 dark:bg-red-400'
      };
      case 'High': return {
        border: 'border-orange-500 dark:border-orange-400',
        background: 'bg-white dark:bg-gray-800',
        inner: 'bg-orange-500 dark:bg-orange-400'
      };
      case 'Moderate': return {
        border: 'border-yellow-500 dark:border-yellow-400',
        background: 'bg-white dark:bg-gray-800',
        inner: 'bg-yellow-500 dark:bg-yellow-400'
      };
      case 'Low': return {
        border: 'border-blue-500 dark:border-blue-400',
        background: 'bg-white dark:bg-gray-800',
        inner: 'bg-blue-500 dark:bg-blue-400'
      };
      default: return {
        border: 'border-gray-500 dark:border-gray-400',
        background: 'bg-white dark:bg-gray-800',
        inner: 'bg-gray-500 dark:bg-gray-400'
      };
    }
  };

  const getAlertBackground = () => {
    if (alert.status === 'resolved') {
      return 'bg-gray-50/50 border-gray-200/50 dark:bg-gray-900/30 dark:border-gray-700/50';
    }
    switch (alert.severity) {
      case 'Severe': return 'bg-red-50/70 border-red-200/70 dark:bg-red-950/30 dark:border-red-800/50';
      case 'High': return 'bg-orange-50/70 border-orange-200/70 dark:bg-orange-950/30 dark:border-orange-800/50';
      case 'Moderate': return 'bg-yellow-50/70 border-yellow-200/70 dark:bg-yellow-950/30 dark:border-yellow-800/50';
      case 'Low': return 'bg-blue-50/70 border-blue-200/70 dark:bg-blue-950/30 dark:border-blue-800/50';
      default: return 'bg-gray-50/70 border-gray-200/70 dark:bg-gray-900/30 dark:border-gray-700/50';
    }
  };

  const dotColors = getDotColors();

  return (
    <div className={`relative pl-8 pb-6 border-l-2 transition-all duration-300 hover:border-opacity-100 ${getTimelineColors()}`}>
      {/* Enhanced timeline dot with pulse effect for critical alerts */}
      <div className={`absolute -left-[9px] top-3 w-4 h-4 rounded-full border-2 ${dotColors.border} ${dotColors.background} ${
        alert.status === 'open' && (alert.severity === 'Severe' || alert.severity === 'High') ? 'animate-pulse' : ''
      }`}>
        <div className={`w-1.5 h-1.5 rounded-full mx-auto mt-[3px] ${dotColors.inner}`} />
      </div>

      {/* Enhanced alert card with better shadows and hover effects */}
      <div className={`rounded-lg border p-4 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ${getAlertBackground()}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Alert header with better spacing */}
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              {severityIcons[alert.severity]}
              <h4 className="font-semibold text-sm leading-tight">{alert.title}</h4>
              <Badge
                variant={alert.severity === 'Severe' ? 'destructive' : 'secondary'}
                className="text-xs px-2 py-0.5 font-medium"
              >
                {alert.severity}
              </Badge>
              <Badge
                variant="outline"
                className="text-xs px-2 py-0.5"
              >
                {alert.type}
              </Badge>
            </div>

            {/* Alert description with better typography */}
            <p className="text-sm text-muted-foreground mb-3 leading-relaxed">{alert.description}</p>

            {/* Enhanced metadata grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-4 gap-y-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <MapPin className="h-3 w-3 flex-shrink-0" />
                <span className="truncate">{getAlertLocation(alert)}</span>
              </div>

              {alert.eta && (
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3 w-3 flex-shrink-0" />
                  <span className="truncate">ETA: {alert.eta}</span>
                </div>
              )}

              {alert.crewId && (
                <div className="flex items-center gap-1.5">
                  <User className="h-3 w-3 flex-shrink-0" />
                  <span className="truncate">{alert.crewId}</span>
                </div>
              )}

              <div className="flex items-center gap-1.5">
                <Clock className="h-3 w-3 flex-shrink-0" />
                <span>{format(new Date(alert.timestamp), 'MMM d, HH:mm')}</span>
              </div>
            </div>
          </div>

          {/* Enhanced action buttons */}
          <div className="flex items-center gap-2 ml-4 flex-shrink-0">
            {statusIcons[alert.status]}
            {alert.status === 'open' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onAcknowledge(alert.id)}
                className="h-7 px-3 text-xs hover:bg-primary hover:text-primary-foreground transition-colors"
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