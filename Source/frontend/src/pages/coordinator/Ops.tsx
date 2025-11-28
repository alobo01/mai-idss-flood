
import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LiveOpsBoard } from '@/components/LiveOpsBoard';
import { AlertsTimeline } from '@/components/AlertsTimeline';
import { CommunicationsPanel } from '@/components/CommunicationsPanel';
import { Radio, AlertTriangle, Activity } from 'lucide-react';

export function CoordinatorOps() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Live Operations Center</h1>
        <p className="text-muted-foreground">Real-time coordination and monitoring</p>
      </div>

      <Tabs defaultValue="dashboard" className="space-y-4">
        <TabsList>
          <TabsTrigger value="dashboard" className="flex items-center space-x-2">
            <Activity className="h-4 w-4" />
            <span>Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4" />
            <span>Alerts Timeline</span>
          </TabsTrigger>
          <TabsTrigger value="comms" className="flex items-center space-x-2">
            <Radio className="h-4 w-4" />
            <span>Communications</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <LiveOpsBoard />
        </TabsContent>

        <TabsContent value="alerts">
          <AlertsTimeline />
        </TabsContent>

        <TabsContent value="comms">
          <CommunicationsPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}