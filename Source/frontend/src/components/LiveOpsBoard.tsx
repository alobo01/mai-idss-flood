import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  MapPin,
  Users,
  AlertTriangle,
  Radio,
  TrendingUp,
  Activity,
  Clock,
  Zap,
  Shield,
  Gauge,
  Phone,
  MessageSquare
} from 'lucide-react';
import { useAlerts, useGauges, useCommunications, useResources } from '@/hooks/useApiData';
import { format } from 'date-fns';
import type { Alert, Gauge as GaugeType, Communication, Resources } from '@/types';

interface LiveOpsBoardProps {
  className?: string;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
  };
  color?: string;
  description?: string;
}

function MetricCard({ title, value, icon, trend, color = 'default', description }: MetricCardProps) {
  const getTrendIcon = () => {
    switch (trend?.direction) {
      case 'up':
        return <TrendingUp className="h-3 w-3 text-red-500" />;
      case 'down':
        return <TrendingUp className="h-3 w-3 text-green-500 rotate-180" />;
      default:
        return <TrendingUp className="h-3 w-3 text-gray-500 rotate-90" />;
    }
  };

  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div className="flex flex-col items-end space-y-1">
            <div className={`p-2 rounded-lg ${
              color === 'red' ? 'bg-red-100 text-red-600' :
              color === 'orange' ? 'bg-orange-100 text-orange-600' :
              color === 'blue' ? 'bg-blue-100 text-blue-600' :
              color === 'green' ? 'bg-green-100 text-green-600' :
              'bg-gray-100 text-gray-600'
            }`}>
              {icon}
            </div>
            {trend && (
              <div className="flex items-center space-x-1 text-xs">
                {getTrendIcon()}
                <span>{trend.value}%</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function LiveOpsBoard({ className = '' }: LiveOpsBoardProps) {
  const { data: alerts = [], isLoading: alertsLoading } = useAlerts();
  const { data: gauges = [], isLoading: gaugesLoading } = useGauges();
  const { data: communications = [], isLoading: commsLoading } = useCommunications();
  const { data: resources, isLoading: resourcesLoading } = useResources();

  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Calculate metrics
  const activeAlerts = alerts.filter(a => a.status === 'open');
  const severeAlerts = alerts.filter(a => a.status === 'open' && a.severity === 'Severe');
  const criticalGauges = gauges.filter(g => g.level_m >= g.alert_threshold);
  const deployedCrews = resources?.crews?.filter(c => c.status === 'working' || c.status === 'enroute') || [];
  const availableCrews = resources?.crews?.filter(c => c.status === 'ready') || [];

  // Get recent communications (last 10 minutes)
  const recentCommunications = communications.filter(comm => {
    const commTime = new Date(comm.timestamp);
    const tenMinutesAgo = new Date(currentTime.getTime() - 10 * 60 * 1000);
    return commTime > tenMinutesAgo;
  });

  if (alertsLoading || gaugesLoading || commsLoading || resourcesLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-8 w-8 animate-pulse mx-auto mb-2" />
            <p>Loading Live Operations Board...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with live time */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Live Operations Board</h1>
          <p className="text-muted-foreground">Real-time flood response coordination</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-muted-foreground">Current Time</div>
          <div className="text-lg font-mono font-bold">
            {format(currentTime, 'HH:mm:ss')}
          </div>
          <div className="text-sm text-muted-foreground">
            {format(currentTime, 'MMM d, yyyy')}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Alerts"
          value={activeAlerts.length}
          icon={<AlertTriangle className="h-5 w-5" />}
          color={severeAlerts.length > 0 ? 'red' : 'blue'}
          description={`${severeAlerts.length} severe`}
          trend={{
            value: Math.round(Math.random() * 10), // Simulated trend
            direction: 'up'
          }}
        />

        <MetricCard
          title="Crews Deployed"
          value={deployedCrews.length}
          icon={<Users className="h-5 w-5" />}
          color="orange"
          description={`${availableCrews.length} available`}
        />

        <MetricCard
          title="Critical Gauges"
          value={criticalGauges.length}
          icon={<Gauge className="h-5 w-5" />}
          color={criticalGauges.length > 0 ? 'red' : 'green'}
          description={`of ${gauges.length} total`}
        />

        <MetricCard
          title="Recent Communications"
          value={recentCommunications.length}
          icon={<MessageSquare className="h-5 w-5" />}
          color="blue"
          description="last 10 minutes"
        />
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Critical Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span>Critical Alerts</span>
              {severeAlerts.length > 0 && (
                <Badge variant="destructive">{severeAlerts.length}</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {severeAlerts.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No critical alerts</p>
                </div>
              ) : (
                severeAlerts.slice(0, 3).map(alert => (
                  <div key={alert.id} className="border-l-4 border-red-500 bg-red-50 p-3 rounded-r">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-sm">{alert.title}</h4>
                        <p className="text-xs text-muted-foreground mt-1">{alert.description}</p>
                        <div className="flex items-center space-x-2 mt-2 text-xs text-muted-foreground">
                          <MapPin className="h-3 w-3" />
                          <span>{alert.zoneId}</span>
                          {alert.eta && (
                            <>
                              <Clock className="h-3 w-3 ml-2" />
                              <span>ETA: {alert.eta}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <Badge variant="destructive" className="text-xs">
                        {alert.severity}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Gauge Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Gauge className="h-5 w-5 text-blue-500" />
              <span>River Gauges</span>
              {criticalGauges.length > 0 && (
                <Badge variant="destructive">{criticalGauges.length} critical</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {gauges.slice(0, 5).map(gauge => {
                const percentage = (gauge.level_m / gauge.critical_threshold) * 100;
                const isCritical = gauge.level_m >= gauge.alert_threshold;
                const isNearCritical = gauge.level_m >= gauge.alert_threshold * 0.8;

                return (
                  <div key={gauge.id} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{gauge.name}</span>
                      <span className={`font-mono ${
                        isCritical ? 'text-red-600' : isNearCritical ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {gauge.level_m.toFixed(1)}m
                      </span>
                    </div>
                    <Progress
                      value={Math.min(percentage, 100)}
                      className={`h-2 ${
                        isCritical ? '[&>div]:bg-red-500' :
                        isNearCritical ? '[&>div]:bg-yellow-500' :
                        '[&>div]:bg-green-500'
                      }`}
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Alert: {gauge.alert_threshold.toFixed(1)}m</span>
                      <span>Critical: {gauge.critical_threshold.toFixed(1)}m</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Recent Communications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Radio className="h-5 w-5 text-green-500" />
              <span>Recent Communications</span>
              {recentCommunications.length > 0 && (
                <Badge variant="secondary">{recentCommunications.length}</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {recentCommunications.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  <Phone className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No recent communications</p>
                </div>
              ) : (
                recentCommunications.slice(0, 10).map(comm => (
                  <div key={comm.id} className="border-l-4 border-green-500 bg-green-50 p-3 rounded-r">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-medium text-sm">{comm.from}</span>
                          <Badge variant="outline" className="text-xs">
                            {comm.channel}
                          </Badge>
                        </div>
                        <p className="text-sm">{comm.text}</p>
                        <div className="text-xs text-muted-foreground mt-1">
                          {format(new Date(comm.timestamp), 'HH:mm:ss')}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resource Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5 text-purple-500" />
            <span>Resource Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Crew Status */}
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Crew Status</h4>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Ready:</span>
                  <span className="font-medium text-green-600">{availableCrews.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Deployed:</span>
                  <span className="font-medium text-orange-600">{deployedCrews.length}</span>
                </div>
              </div>
            </div>

            {/* Equipment Status */}
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Equipment Status</h4>
              {resources?.equipment && (
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Available:</span>
                    <span className="font-medium text-green-600">
                      {resources.equipment.filter(e => e.status === 'available').length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Deployed:</span>
                    <span className="font-medium text-orange-600">
                      {resources.equipment.filter(e => e.status === 'deployed').length}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Active Zones */}
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Active Zones</h4>
              <div className="flex flex-wrap gap-1">
                {Array.from(new Set(activeAlerts.map(a => a.zoneId))).map(zoneId => (
                  <Badge key={zoneId} variant="outline" className="text-xs">
                    {zoneId}
                  </Badge>
                ))}
                {activeAlerts.length === 0 && (
                  <span className="text-sm text-muted-foreground">No active zones</span>
                )}
              </div>
            </div>

            {/* System Health */}
            <div className="space-y-2">
              <h4 className="font-medium text-sm">System Health</h4>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-green-600">All systems operational</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}