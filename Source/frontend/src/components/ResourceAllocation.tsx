import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  MoveHorizontal,
  Clock,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useResources, useZones } from '@/hooks/useApiData';
import { usePipelineScenarios, useScenarioAllocations } from '@/hooks/usePipelineData';
import type { Crew, Equipment, PipelineZoneAllocationSummary, ZoneProperties } from '@/types';

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

type PriorityZone = PipelineZoneAllocationSummary & {
  properties: ZoneProperties | null;
};

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
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);

  const { data: resources, isLoading: resourcesLoading } = useResources();
  const { data: zones, isLoading: zonesLoading } = useZones();
  const {
    data: pipelineScenarios = [],
    isLoading: pipelineScenariosLoading,
  } = usePipelineScenarios();

  useEffect(() => {
    if (!selectedScenario && pipelineScenarios.length > 0) {
      setSelectedScenario(pipelineScenarios[0].name);
    }
  }, [pipelineScenarios, selectedScenario]);

  const {
    data: pipelineAllocations,
    isLoading: pipelineAllocationsLoading,
    error: pipelineAllocationsError,
  } = useScenarioAllocations({
    scenario: selectedScenario,
    latest: true,
    limit: 1000,
    enabled: Boolean(selectedScenario),
  });

  const isLoadingState =
    resourcesLoading ||
    zonesLoading ||
    pipelineScenariosLoading ||
    (Boolean(selectedScenario) && pipelineAllocationsLoading);

  if (isLoadingState) {
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

  const deployedCrews = resources?.crews?.filter(c => c.status === 'working' || c.status === 'enroute') || [];
  const deployedEquipment = resources?.equipment?.filter(e => e.status === 'deployed') || [];

  const zoneIndex = useMemo(() => {
    const index = new Map<string, ZoneProperties>();
    zones?.features.forEach(feature => {
      index.set(feature.properties.id, feature.properties);
    });
    return index;
  }, [zones]);

  const pipelineSummary = pipelineAllocations?.summary;
  const priorityZones = useMemo<PriorityZone[]>(() => {
    if (!pipelineSummary?.zones) {
      return [];
    }

    return pipelineSummary.zones.map(zone => ({
      ...zone,
      properties: zoneIndex.get(zone.zone_id) ?? null,
    }));
  }, [pipelineSummary, zoneIndex]);

  const pipelineZoneSummaryMap = useMemo(() => {
    const map = new Map<string, (typeof priorityZones)[number]>();
    priorityZones.forEach(zone => map.set(zone.zone_id, zone));
    return map;
  }, [priorityZones]);

  const pipelineTotals = pipelineSummary?.totals;
  const recommendedUnits = pipelineTotals?.total_units ?? 0;
  const formattedRecommendedUnits = recommendedUnits.toLocaleString();
  const criticalUnits = pipelineTotals?.critical_units ?? 0;
  const formattedCriticalUnits = criticalUnits.toLocaleString();
  const snapshotTimestamp = pipelineAllocations?.meta.time_range.end ?? null;
  const snapshotRelative = snapshotTimestamp
    ? formatDistanceToNow(new Date(snapshotTimestamp), { addSuffix: true })
    : null;
  const snapshotAbsolute = snapshotTimestamp ? new Date(snapshotTimestamp).toLocaleString() : '—';
  const selectedScenarioMeta =
    pipelineScenarios.find(scenario => scenario.name === selectedScenario) || null;
  const lastRunRelative = selectedScenarioMeta?.last_run_at
    ? formatDistanceToNow(new Date(selectedScenarioMeta.last_run_at), { addSuffix: true })
    : null;
  const pipelineCriticalZones = priorityZones.filter(zone =>
    zone.is_critical_infra || zone.last_impact?.toLowerCase().includes('crit')
  ).length;
  const pipelineErrorMessage = pipelineAllocationsError instanceof Error
    ? pipelineAllocationsError.message
    : 'Failed to load pipeline allocations';
  const returnedRows = pipelineAllocations?.meta.returned_rows ?? 0;
  const totalRows = pipelineAllocations?.meta.total_rows ?? 0;
  const formattedReturnedRows = returnedRows.toLocaleString();
  const formattedTotalRows = totalRows.toLocaleString();
  const allocationFile = pipelineAllocations?.meta.file ?? null;
  const hasPipelineData = Boolean(pipelineAllocations);
  const scenarioSelectValue = selectedScenario ?? undefined;

  const formatImpactLabel = (impact?: string | null) => {
    if (!impact) return 'Normal';
    return impact
      .toLowerCase()
      .split('_')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  };

  const getImpactBadgeVariant = (impact?: string | null) => {
    if (!impact) return 'outline';
    const label = impact.toUpperCase();
    if (label.includes('CRIT')) return 'destructive';
    if (label.includes('HIGH')) return 'default';
    if (label.includes('MODERATE') || label.includes('ELEVATED')) return 'secondary';
    return 'outline';
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Resource Allocation</h1>
          <p className="text-muted-foreground">Manage crews and equipment deployment</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Pipeline scenario</span>
          <Select
            value={scenarioSelectValue}
            onValueChange={value => setSelectedScenario(value)}
            disabled={!pipelineScenarios.length}
          >
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select scenario" />
            </SelectTrigger>
            <SelectContent>
              {pipelineScenarios.map(scenario => (
                <SelectItem key={scenario.name} value={scenario.name}>
                  {scenario.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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
              <p className="text-sm font-medium text-muted-foreground">Pipeline Priority Zones</p>
              <p className="text-2xl font-bold">{priorityZones.length}</p>
              <p className="text-xs text-muted-foreground">
                Critical focus: {pipelineCriticalZones}
              </p>
              <p className="text-xs text-muted-foreground">
                {snapshotRelative ? `Snapshot ${snapshotRelative}` : 'Awaiting pipeline output'}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <Clock className="h-8 w-8 text-indigo-500" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">Units Recommended</p>
              <p className="text-2xl font-bold">{formattedRecommendedUnits}</p>
              <p className="text-xs text-muted-foreground">
                {lastRunRelative ? `Last run ${lastRunRelative}` : 'Waiting for pipeline run'}
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

      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Pipeline Snapshot</span>
            {allocationFile && (
              <Badge variant="outline" className="text-xs">
                {allocationFile}
              </Badge>
            )}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Live recommendations from the latest pipeline allocator run.
          </p>
        </CardHeader>
        <CardContent>
          {!pipelineScenarios.length ? (
            <p className="text-sm text-muted-foreground">
              No pipeline scenarios detected. Run `pipeline_v2` or configure scenarios in
              <code className="mx-1">pipeline_v2/config.yaml</code>.
            </p>
          ) : pipelineAllocationsError ? (
            <p className="text-sm text-red-600">{pipelineErrorMessage}</p>
          ) : !hasPipelineData ? (
            <p className="text-sm text-muted-foreground">
              Select a scenario to load the latest allocation snapshot.
            </p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs text-muted-foreground">Scenario</p>
                <p className="text-lg font-semibold">{selectedScenario ?? '—'}</p>
                <p className="text-xs text-muted-foreground">
                  {allocationFile || 'No allocation file detected'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Snapshot time</p>
                <p className="text-lg font-semibold">{snapshotAbsolute}</p>
                <p className="text-xs text-muted-foreground">
                  {snapshotRelative || 'Awaiting pipeline output'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Units (critical)</p>
                <p className="text-lg font-semibold">
                  {formattedRecommendedUnits}
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({formattedCriticalUnits} critical)
                  </span>
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Records loaded</p>
                <p className="text-lg font-semibold">{formattedReturnedRows}</p>
                <p className="text-xs text-muted-foreground">
                  of {formattedTotalRows} rows
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pipeline Priority Zones */}
      {priorityZones.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span>Pipeline Priority Zones</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {priorityZones.map(zone => (
                <Card
                  key={zone.zone_id}
                  className={zone.is_critical_infra ? 'border-red-200 bg-red-50' : ''}
                >
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{zone.properties?.name || zone.zone_name}</h4>
                        <p className="text-xs text-muted-foreground">{zone.zone_id}</p>
                      </div>
                      <Badge variant={getImpactBadgeVariant(zone.last_impact)}>
                        {formatImpactLabel(zone.last_impact)}
                      </Badge>
                    </div>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <p>Units recommended: {zone.latest_units.toLocaleString()}</p>
                      <p>
                        Population:{' '}
                        {typeof zone.properties?.population === 'number'
                          ? zone.properties.population.toLocaleString()
                          : '—'}
                      </p>
                      <p>
                        Critical assets: {zone.properties?.critical_assets?.length ?? 0}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => setSelectedZone(zone.zone_id)}
                    >
                      <MapPin className="h-3 w-3 mr-1" />
                      View Details
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="text-sm text-muted-foreground p-6">
            {pipelineScenarios.length ? (
              'Pipeline outputs have not generated allocation data yet. Trigger a run to populate priority zones.'
            ) : (
              <span>
                Add scenarios to <code className="mx-1">pipeline_v2/config.yaml</code> to enable pipeline-driven
                priorities.
              </span>
            )}
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
              const pipelineZone = pipelineZoneSummaryMap.get(zone.properties.id);

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

                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center space-x-1">
                        <Activity className="h-3 w-3" />
                        <span>Pipeline Units:</span>
                      </span>
                      <span className="font-medium">
                        {pipelineZone ? pipelineZone.latest_units.toLocaleString() : 0}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Impact</span>
                      <Badge variant={getImpactBadgeVariant(pipelineZone?.last_impact)}>
                        {pipelineZone ? formatImpactLabel(pipelineZone.last_impact) : 'Normal'}
                      </Badge>
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