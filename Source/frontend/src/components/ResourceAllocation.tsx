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
  Users,
  Truck,
  MapPin,
  Activity,
  Plus,
  MoveHorizontal,
  Clock,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { useResources, useZones, useRiskData } from '@/hooks/useApiData';
import type { Resources, Crew, Equipment, ZoneProperties, RiskPoint } from '@/types';

interface ResourceAllocationProps {
  className?: string;
}

interface ResourceCardProps {
  title: string;
  icon: React.ReactNode;
  items: (Crew | Equipment)[];
  type: 'crew' | 'equipment';
  onDeploy?: (resource: string, target: string) => void;
}

function ResourceCard({ title, icon, items, type, onDeploy }: ResourceCardProps) {
  const [selectedResource, setSelectedResource] = useState<string | null>(null);
  const [showDeployDialog, setShowDeployDialog] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800 border-green-200';
      case 'enroute': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'working': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'maintenance': return 'bg-red-100 text-red-800 border-red-200';
      case 'deployed': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleDeploy = (resourceId: string) => {
    setSelectedResource(resourceId);
    setShowDeployDialog(true);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            {icon}
            <span>{title}</span>
            <Badge variant="secondary" className="ml-2">
              {items.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-3">
              {items.map((resource) => (
                <div
                  key={resource.id}
                  className={`border rounded-lg p-3 hover:bg-gray-50 cursor-pointer ${
                    selectedResource === resource.id ? 'ring-2 ring-blue-500' : ''
                  }`}
                  onClick={() => setSelectedResource(resource.id)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-sm">
                        {type === 'crew' ? (resource as Crew).name : (resource as Equipment).type}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        {type === 'crew'
                          ? `Skills: ${(resource as Crew).skills.join(', ')}`
                          : `Subtype: ${(resource as Equipment).subtype || 'N/A'}`
                        }
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Depot: {resource.depot}
                      </p>
                    </div>
                    <div className="flex flex-col items-end space-y-2">
                      <Badge variant="outline" className={getStatusColor(resource.status)}>
                        {resource.status}
                      </Badge>
                      {(resource.status === 'ready' || resource.status === 'available') && onDeploy && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeploy(resource.id);
                          }}
                          className="h-6 px-2 text-xs"
                        >
                          <MoveHorizontal className="h-3 w-3 mr-1" />
                          Deploy
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Deploy Dialog */}
      <Dialog open={showDeployDialog} onOpenChange={setShowDeployDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Deploy Resource</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Resource</label>
              <p className="text-sm text-muted-foreground">
                {items.find(r => r.id === selectedResource)?.id || 'Unknown'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Target Zone</label>
              <select className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm">
                <option value="">Select zone...</option>
                {/* Zone options would be populated here */}
              </select>
            </div>
            <Button
              onClick={() => {
                if (onDeploy && selectedResource) {
                  onDeploy(selectedResource, 'target-zone');
                  setShowDeployDialog(false);
                }
              }}
              className="w-full"
            >
              Deploy Resource
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

export function ResourceAllocation({ className = '' }: ResourceAllocationProps) {
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  const { data: resources, isLoading: resourcesLoading } = useResources();
  const { data: zones, isLoading: zonesLoading } = useZones();
  const { data: riskData, isLoading: riskLoading } = useRiskData();

  if (resourcesLoading || zonesLoading || riskLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-8 w-8 animate-pulse mx-auto mb-2" />
            <p>Loading Resource Allocation...</p>
          </div>
        </div>
      </div>
    );
  }

  // Get high-risk zones for prioritization
  const highRiskZones = zones?.features.filter(zone => {
    const risk = riskData?.find(r => r.zoneId === zone.properties.id);
    return risk && (risk.risk > 0.5 || risk.thresholdBand === 'Severe');
  }) || [];

  const deployedCrews = resources?.crews?.filter(c => c.status === 'working' || c.status === 'enroute') || [];
  const deployedEquipment = resources?.equipment?.filter(e => e.status === 'deployed') || [];

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h1 className="text-3xl font-bold">Resource Allocation</h1>
        <p className="text-muted-foreground">Manage crews and equipment deployment</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <Users className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Crews</p>
              <p className="text-2xl font-bold">{resources?.crews?.length || 0}</p>
              <p className="text-xs text-muted-foreground">
                {deployedCrews.length} deployed
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <Truck className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Equipment</p>
              <p className="text-2xl font-bold">{resources?.equipment?.length || 0}</p>
              <p className="text-xs text-muted-foreground">
                {deployedEquipment.length} deployed
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">High Risk Zones</p>
              <p className="text-2xl font-bold">{highRiskZones.length}</p>
              <p className="text-xs text-muted-foreground">
                Priority for deployment
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <CheckCircle className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">Available Resources</p>
              <p className="text-2xl font-bold">
                {(resources?.crews?.filter(c => c.status === 'ready').length || 0) +
                 (resources?.equipment?.filter(e => e.status === 'available').length || 0)}
              </p>
              <p className="text-xs text-muted-foreground">
                Ready to deploy
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* High Risk Zones Priority */}
      {highRiskZones.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span>Priority Zones for Deployment</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {highRiskZones.map((zone) => {
                const risk = riskData?.find(r => r.zoneId === zone.properties.id);
                return (
                  <Card key={zone.properties.id} className="border-red-200 bg-red-50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{zone.properties.name}</h4>
                        <Badge variant="destructive">
                          {risk?.thresholdBand}
                        </Badge>
                      </div>
                      <div className="space-y-1 text-sm text-muted-foreground">
                        <p>Population: {zone.properties.population.toLocaleString()}</p>
                        <p>Risk Level: {risk ? `${(risk.risk * 100).toFixed(0)}%` : 'N/A'}</p>
                        <p>Critical Assets: {zone.properties.critical_assets.length}</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-3"
                        onClick={() => setSelectedZone(zone.properties.id)}
                      >
                        <MapPin className="h-3 w-3 mr-1" />
                        View Details
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Resource Management */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ResourceCard
          title="Crew Members"
          icon={<Users className="h-5 w-5 text-blue-500" />}
          items={resources?.crews || []}
          type="crew"
          onDeploy={(resourceId, target) => {
            console.log(`Deploying crew ${resourceId} to ${target}`);
            // Implementation would handle the actual deployment
          }}
        />

        <ResourceCard
          title="Equipment"
          icon={<Truck className="h-5 w-5 text-green-500" />}
          items={resources?.equipment || []}
          type="equipment"
          onDeploy={(resourceId, target) => {
            console.log(`Deploying equipment ${resourceId} to ${target}`);
            // Implementation would handle the actual deployment
          }}
        />
      </div>

      {/* Deployment Zones Map */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MapPin className="h-5 w-5" />
            <span>Deployment Zones</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {zones?.features.map((zone) => {
              const zoneCrews = deployedCrews.filter(crew =>
                // This would be based on actual deployment data
                crew.depot === zone.properties.id
              );
              const zoneEquipment = deployedEquipment.filter(equipment =>
                equipment.depot === zone.properties.id
              );

              return (
                <Card key={zone.properties.id} className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">{zone.properties.name}</h4>
                    <Badge variant="outline">
                      {zone.properties.id}
                    </Badge>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center space-x-1">
                        <Users className="h-3 w-3" />
                        <span>Crews:</span>
                      </span>
                      <span className="font-medium">{zoneCrews.length}</span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center space-x-1">
                        <Truck className="h-3 w-3" />
                        <span>Equipment:</span>
                      </span>
                      <span className="font-medium">{zoneEquipment.length}</span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center space-x-1">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Population:</span>
                      </span>
                      <span className="font-medium">{zone.properties.population.toLocaleString()}</span>
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-3"
                    onClick={() => setSelectedZone(zone.properties.id)}
                  >
                    Manage Deployment
                  </Button>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}