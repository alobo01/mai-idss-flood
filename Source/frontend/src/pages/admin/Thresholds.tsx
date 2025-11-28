import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, Info, Settings } from 'lucide-react';

export function AdminThresholds() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Threshold Configuration</h1>

      <Alert className="mb-6">
        <Info className="h-4 w-4" />
        <AlertDescription>
          Configure risk thresholds, gauge monitoring levels, and automated alert rules for the flood prediction system.
          These settings determine when alerts are triggered and how severe events are classified.
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="risk" className="space-y-6">
        <TabsList>
          <TabsTrigger value="risk">Risk Thresholds</TabsTrigger>
          <TabsTrigger value="gauges">Gauge Thresholds</TabsTrigger>
          <TabsTrigger value="alerts">Alert Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="risk">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Risk Band Thresholds
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-4 h-4 rounded bg-green-500"></div>
                      <Badge className="bg-green-100 text-green-800">Low</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">0% - 25% risk level</p>
                    <p className="text-xs mt-1">Low flood risk areas</p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-4 h-4 rounded bg-yellow-500"></div>
                      <Badge className="bg-yellow-100 text-yellow-800">Moderate</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">25% - 50% risk level</p>
                    <p className="text-xs mt-1">Moderate flood risk areas</p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-4 h-4 rounded bg-red-500"></div>
                      <Badge className="bg-red-100 text-red-800">Severe</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">75% - 100% risk level</p>
                    <p className="text-xs mt-1">Severe flood risk areas</p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Risk thresholds determine when alerts are automatically triggered based on predicted flood levels.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="gauges">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Gauge Monitoring Thresholds
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">River Station A</h4>
                    <p className="text-sm"><strong>Alert:</strong> 3.5 meters</p>
                    <p className="text-sm"><strong>Critical:</strong> 5.0 meters</p>
                    <Badge variant="outline" className="mt-2">Active Monitoring</Badge>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">River Station B</h4>
                    <p className="text-sm"><strong>Alert:</strong> 2.8 meters</p>
                    <p className="text-sm"><strong>Critical:</strong> 4.2 meters</p>
                    <Badge variant="outline" className="mt-2">Active Monitoring</Badge>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Water level gauges provide real-time monitoring of river heights and trigger alerts when thresholds are exceeded.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Automated Alert Rules
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">High Risk Alert</h4>
                      <Badge className="bg-orange-100 text-orange-800">High</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">Trigger: Risk &gt; 75%</p>
                    <div className="flex flex-wrap gap-1">
                      <Badge variant="outline" className="text-xs">Dashboard</Badge>
                      <Badge variant="outline" className="text-xs">Email</Badge>
                    </div>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">Critical Alert</h4>
                      <Badge className="bg-red-100 text-red-800">Severe</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">Trigger: Gauge &gt; Critical</p>
                    <div className="flex flex-wrap gap-1">
                      <Badge variant="outline" className="text-xs">Dashboard</Badge>
                      <Badge variant="outline" className="text-xs">SMS</Badge>
                      <Badge variant="outline" className="text-xs">Email</Badge>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Alert rules automatically notify response teams when specific conditions are met.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}