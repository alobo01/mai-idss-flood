
import React from 'react';
import { AlertsTimeline } from '@/components/AlertsTimeline';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, TrendingUp, Clock, Filter } from 'lucide-react';
import { useAlerts, useResources } from '@/hooks/useApiData';
import { format } from 'date-fns';

export function PlannerAlerts() {
  const { data: alerts = [] } = useAlerts();
  const { data: resources } = useResources();

  // Calculate alert metrics
  const activeAlerts = alerts.filter(alert => alert.status === 'open').length;
  const highSeverityAlerts = alerts.filter(alert =>
    alert.status === 'open' && (alert.severity === 'High' || alert.severity === 'Severe')
  ).length;
  const acknowledgedAlerts = alerts.filter(alert => alert.status === 'acknowledged').length;

  // Get recent alerts (last 24 hours)
  const recentAlerts = alerts.filter(alert =>
    new Date(alert.timestamp) > new Date(Date.now() - 24 * 60 * 60 * 1000)
  );

  // Alert trends by severity
  const alertTrends = {
    Severe: alerts.filter(a => a.severity === 'Severe' && a.status === 'open').length,
    High: alerts.filter(a => a.severity === 'High' && a.status === 'open').length,
    Moderate: alerts.filter(a => a.severity === 'Moderate' && a.status === 'open').length,
    Low: alerts.filter(a => a.severity === 'Low' && a.status === 'open').length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Alerts & Intelligence</h1>
        <p className="text-muted-foreground">Strategic alert monitoring and analysis</p>
      </div>

      {/* Executive Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <div className="text-2xl font-bold">{activeAlerts}</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Requiring attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Critical Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-orange-500" />
              <div className="text-2xl font-bold text-orange-600">{highSeverityAlerts}</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">High/Severe alerts</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">In Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-yellow-500" />
              <div className="text-2xl font-bold text-yellow-600">{acknowledgedAlerts}</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Being addressed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">24h Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-blue-500" />
              <div className="text-2xl font-bold">{recentAlerts.length}</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Last 24 hours</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="timeline" className="space-y-4">
        <TabsList>
          <TabsTrigger value="timeline">Timeline View</TabsTrigger>
          <TabsTrigger value="analysis">Analysis Dashboard</TabsTrigger>
          <TabsTrigger value="zones">Zone Intelligence</TabsTrigger>
        </TabsList>

        <TabsContent value="timeline">
          <AlertsTimeline />
        </TabsContent>

        <TabsContent value="analysis">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Alert Severity Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Alert Severity Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(alertTrends).map(([severity, count]) => {
                    const total = Object.values(alertTrends).reduce((sum, c) => sum + c, 0);
                    const percentage = total > 0 ? (count / total) * 100 : 0;
                    const colorClass = severity === 'Severe' ? 'bg-red-500 dark:bg-red-400' :
                                     severity === 'High' ? 'bg-orange-500 dark:bg-orange-400' :
                                     severity === 'Moderate' ? 'bg-yellow-500 dark:bg-yellow-400' :
                                     'bg-blue-500 dark:bg-blue-400';

                    return (
                      <div key={severity} className="flex items-center space-x-3">
                        <div className="w-16 text-sm font-medium">{severity}</div>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4 relative overflow-hidden">
                          <div
                            className={`${colorClass} h-4 rounded-full transition-all duration-300 ease-out`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <div className="text-sm font-medium w-8 text-right">{count}</div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Alert Types Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Alert Categories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(
                    alerts.reduce((acc, alert) => {
                      acc[alert.type] = (acc[alert.type] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                      <span className="text-sm font-medium">{type}</span>
                      <Badge variant="secondary" className="bg-gray-100 dark:bg-gray-700">{count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Resource Status */}
            <Card>
              <CardHeader>
                <CardTitle>Resource Availability</CardTitle>
              </CardHeader>
              <CardContent>
                {resources && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-2 rounded-lg bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
                      <span className="text-sm font-medium text-green-800 dark:text-green-200">Available Crews</span>
                      <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                        {resources.crews.filter(c => c.status === 'ready').length}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded-lg bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800">
                      <span className="text-sm font-medium text-orange-800 dark:text-orange-200">Deployed Crews</span>
                      <Badge variant="default" className="bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300">
                        {resources.crews.filter(c => c.status === 'working' || c.status === 'enroute').length}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
                      <span className="text-sm font-medium text-blue-800 dark:text-blue-200">Available Equipment</span>
                      <Badge variant="default" className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                        {resources.equipment.filter(e => e.status === 'available').length}
                      </Badge>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Alert Patterns */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="p-3 bg-yellow-50/70 border border-yellow-200/70 dark:bg-yellow-950/30 dark:border-yellow-800/50 rounded-lg">
                    <div className="font-medium text-yellow-800 dark:text-yellow-200">⚠️ High Activity Detected</div>
                    <div className="text-yellow-700 dark:text-yellow-300 mt-1">
                      {recentAlerts.length > 10 ? 'Elevated alert volume in the last 24h' : 'Normal alert volume'}
                    </div>
                  </div>
                  {highSeverityAlerts > 5 && (
                    <div className="p-3 bg-red-50/70 border border-red-200/70 dark:bg-red-950/30 dark:border-red-800/50 rounded-lg">
                      <div className="font-medium text-red-800 dark:text-red-200">🚨 Critical Alert Load</div>
                      <div className="text-red-700 dark:text-red-300 mt-1">
                        Multiple high-severity alerts requiring immediate coordination
                      </div>
                    </div>
                  )}
                  {acknowledgedAlerts > activeAlerts && (
                    <div className="p-3 bg-green-50/70 border border-green-200/70 dark:bg-green-950/30 dark:border-green-800/50 rounded-lg">
                      <div className="font-medium text-green-800 dark:text-green-200">✅ Good Response Rate</div>
                      <div className="text-green-700 dark:text-green-300 mt-1">
                        Teams responding efficiently to incoming alerts
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="zones">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array.from(new Set(alerts.map(a => a.zoneId))).map(zoneId => {
              const zoneAlerts = alerts.filter(a => a.zoneId === zoneId);
              const activeZoneAlerts = zoneAlerts.filter(a => a.status === 'open');
              const criticalZoneAlerts = zoneAlerts.filter(a =>
                a.status === 'open' && (a.severity === 'High' || a.severity === 'Severe')
              );

              const zoneNames: Record<string, string> = {
                'Z-ALFA': 'Riverside North',
                'Z-BRAVO': 'Industrial District',
                'Z-CHARLIE': 'Residential Heights',
                'Z-DELTA': 'Commercial Zone',
                'Z-ECHO': 'Riverside South',
              };

              return (
                <Card key={zoneId} className={criticalZoneAlerts.length > 0 ? 'border-red-200' : ''}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{zoneNames[zoneId] || zoneId}</CardTitle>
                      {criticalZoneAlerts.length > 0 && (
                        <Badge variant="destructive" className="animate-pulse">
                          {criticalZoneAlerts.length} Critical
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Active Alerts</span>
                        <Badge variant={activeZoneAlerts.length > 5 ? 'destructive' : 'secondary'}>
                          {activeZoneAlerts.length}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Last Activity</span>
                        <span className="text-xs">
                          {zoneAlerts.length > 0 ?
                            format(new Date(Math.max(...zoneAlerts.map(a => new Date(a.timestamp).getTime()))), 'MMM d, HH:mm') :
                            'No activity'
                          }
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Priority Level</span>
                        <Badge variant={criticalZoneAlerts.length > 0 ? 'destructive' :
                                      activeZoneAlerts.length > 3 ? 'default' : 'outline'}>
                          {criticalZoneAlerts.length > 0 ? 'Critical' :
                           activeZoneAlerts.length > 3 ? 'High' : 'Normal'}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}