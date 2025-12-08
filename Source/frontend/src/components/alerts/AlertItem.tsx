import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  AlertTriangle,
  Clock,
  MapPin,
  CheckCircle,
  XCircle,
  User
} from 'lucide-react';
import { useAcknowledgeAlert } from '@/hooks/useApiData';
import type { Alert, AlertSeverity, AlertStatus } from '@/types';
import { format } from 'date-fns';
import { useQueryClient } from '@tanstack/react-query';

interface AlertItemProps {
  alert: Alert;
  onAcknowledged?: () => void;
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
  Operational: <Clock className="h-4 w-4 text-gray-500 dark:text-gray-400" />,
};

export function AlertItem({ alert, onAcknowledged }: AlertItemProps) {
  const [acknowledging, setAcknowledging] = useState(false);
  const acknowledgeAlert = useAcknowledgeAlert();
  const queryClient = useQueryClient();

  const handleAcknowledge = async () => {
    if (alert.status === 'acknowledged' || alert.status === 'resolved') return;

    setAcknowledging(true);
    try {
      await acknowledgeAlert.mutateAsync({
        alertId: alert.id,
        acknowledgedBy: 'Current User'
      });

      // Invalidate and refetch alerts
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      onAcknowledged?.();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    } finally {
      setAcknowledging(false);
    }
  };

  return (
    <div className="p-4 border-l-4 border-l-current bg-card hover:bg-accent/50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            {severityIcons[alert.severity]}
            <Badge className={severityColors[alert.severity]} variant="outline">
              {alert.severity}
            </Badge>
            <Badge variant="secondary">{alert.type}</Badge>
            {statusIcons[alert.status]}
          </div>

          <h4 className="font-semibold text-foreground mb-1">{alert.title}</h4>
          <p className="text-sm text-muted-foreground mb-2">{alert.description}</p>

          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              Zone {alert.zoneId}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {format(new Date(alert.timestamp), 'MMM d, HH:mm')}
            </div>
            {alert.crewId && (
              <div className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {alert.crewId}
              </div>
            )}
            {alert.eta && (
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                ETA: {alert.eta}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          {alert.status === 'open' && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleAcknowledge}
              disabled={acknowledging}
              className="shrink-0"
            >
              {acknowledging ? 'Acknowledging...' : 'Acknowledge'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}