import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, Save, RefreshCw, Settings, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ResourceType {
  resource_id: string;
  name: string;
  description: string;
  icon: string;
  display_order: number;
  capacity: number;
}

interface ZoneData {
  zone_id: string;
  name: string;
  river_proximity: number;
  elevation_risk: number;
  pop_density: number;
  crit_infra_score: number;
  hospital_count: number;
  critical_infra: boolean;
}

interface ThresholdConfig {
  id: string;
  name: string;
  value: number;
  unit: string;
  description: string;
}

interface AdministratorPageProps {
  selectedDate?: string;
}

export function AdministratorPage({ selectedDate }: AdministratorPageProps) {
  const [resources, setResources] = useState<ResourceType[]>([]);
  const [zones, setZones] = useState<ZoneData[]>([]);
  const [thresholds, setThresholds] = useState<ThresholdConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  // Edited states
  const [editedCapacities, setEditedCapacities] = useState<Record<string, number>>({});
  const [editedZones, setEditedZones] = useState<Record<string, ZoneData>>({});
  const [editedThresholds, setEditedThresholds] = useState<Record<string, number>>({});

  // Fetch all configuration data
  const fetchConfigData = async () => {
    setLoading(true);
    try {
      // Fetch resources
      const resourceResponse = await fetch('/api/resource-types');
      if (resourceResponse.ok) {
        const resourceData = await resourceResponse.json();
        const resourceRows = resourceData?.data?.rows || resourceData?.rows || [];
        setResources(resourceRows);

        // Initialize edited capacities
        const capacities: Record<string, number> = {};
        resourceRows.forEach((r: ResourceType) => {
          capacities[r.resource_id] = r.capacity || 0;
        });
        setEditedCapacities(capacities);
      }

      // Fetch zones
      const zoneResponse = await fetch('/api/zones');
      if (zoneResponse.ok) {
        const zoneData = await zoneResponse.json();
        const zoneRows = zoneData?.data?.rows || zoneData?.rows || [];
        setZones(zoneRows);

        // Initialize edited zones
        const zonesMap: Record<string, ZoneData> = {};
        zoneRows.forEach((z: ZoneData) => {
          zonesMap[z.zone_id] = { ...z };
        });
        setEditedZones(zonesMap);
      }

      // Fetch thresholds from API
      const thresholdResponse = await fetch('/api/thresholds');
      if (thresholdResponse.ok) {
        const thresholdData = await thresholdResponse.json();
        const thresholdValues = thresholdData?.data?.thresholds || {};

        const defaultThresholds: ThresholdConfig[] = [
          { id: 'flood_minor', name: 'Minor Flood Level', value: thresholdValues.flood_minor || 16, unit: 'ft', description: 'River level for minor flooding' },
          { id: 'flood_moderate', name: 'Moderate Flood Level', value: thresholdValues.flood_moderate || 22, unit: 'ft', description: 'River level for moderate flooding' },
          { id: 'flood_major', name: 'Major Flood Level', value: thresholdValues.flood_major || 28, unit: 'ft', description: 'River level for major flooding' },
          { id: 'critical_probability', name: 'Critical Flood Probability', value: thresholdValues.critical_probability || 0.8, unit: '%', description: 'Probability threshold for critical risk' },
          { id: 'warning_probability', name: 'Warning Flood Probability', value: thresholdValues.warning_probability || 0.6, unit: '%', description: 'Probability threshold for warning level' },
          { id: 'advisory_probability', name: 'Advisory Flood Probability', value: thresholdValues.advisory_probability || 0.3, unit: '%', description: 'Probability threshold for advisory level' },
        ];
        setThresholds(defaultThresholds);

        const thresholdsMap: Record<string, number> = {};
        defaultThresholds.forEach((t) => {
          thresholdsMap[t.id] = t.value;
        });
        setEditedThresholds(thresholdsMap);
      } else {
        // Fallback to default values
        const defaultThresholds: ThresholdConfig[] = [
          { id: 'flood_minor', name: 'Minor Flood Level', value: 16, unit: 'ft', description: 'River level for minor flooding' },
          { id: 'flood_moderate', name: 'Moderate Flood Level', value: 22, unit: 'ft', description: 'River level for moderate flooding' },
          { id: 'flood_major', name: 'Major Flood Level', value: 28, unit: 'ft', description: 'River level for major flooding' },
          { id: 'critical_probability', name: 'Critical Flood Probability', value: 0.8, unit: '%', description: 'Probability threshold for critical risk' },
          { id: 'warning_probability', name: 'Warning Flood Probability', value: 0.6, unit: '%', description: 'Probability threshold for warning level' },
          { id: 'advisory_probability', name: 'Advisory Flood Probability', value: 0.3, unit: '%', description: 'Probability threshold for advisory level' },
        ];
        setThresholds(defaultThresholds);

        const thresholdsMap: Record<string, number> = {};
        defaultThresholds.forEach((t) => {
          thresholdsMap[t.id] = t.value;
        });
        setEditedThresholds(thresholdsMap);
      }

    } catch (error) {
      console.error('Failed to fetch configuration data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load configuration data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigData();
  }, []);

  const handleCapacityChange = (resourceId: string, value: string) => {
    const numValue = parseInt(value) || 0;
    setEditedCapacities(prev => ({ ...prev, [resourceId]: numValue }));
  };

  const handleZoneChange = (zoneId: string, field: keyof ZoneData, value: string | number | boolean) => {
    setEditedZones(prev => ({
      ...prev,
      [zoneId]: {
        ...prev[zoneId],
        [field]: field === 'critical_infra' ? Boolean(value) :
                 field === 'hospital_count' ? parseInt(String(value)) || 0 :
                 typeof value === 'string' ? parseFloat(value) || 0 : value
      }
    }));
  };

  const handleThresholdChange = (thresholdId: string, value: string) => {
    const numValue = parseFloat(value) || 0;
    setEditedThresholds(prev => ({ ...prev, [thresholdId]: numValue }));
  };

  const saveResourceCapacities = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/resource-types/capacities', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ capacities: editedCapacities }),
      });

      if (!response.ok) throw new Error('Failed to update capacities');

      const data = await response.json();
      setResources(data.resources);

      toast({
        title: 'Success',
        description: `Updated ${data.updated_count} resource capacities`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update resource capacities',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const saveZoneParameters = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/zones/parameters', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zones: editedZones }),
      });

      if (!response.ok) throw new Error('Failed to update zone parameters');

      const data = await response.json();
      setZones(data.zones);

      toast({
        title: 'Success',
        description: `Updated parameters for ${data.updated_count} zones`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update zone parameters',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const saveThresholds = async () => {
    setSaving(true);
    try {
      const thresholdData = {
        flood_minor: editedThresholds.flood_minor || 16,
        flood_moderate: editedThresholds.flood_moderate || 22,
        flood_major: editedThresholds.flood_major || 28,
        critical_probability: editedThresholds.critical_probability || 0.8,
        warning_probability: editedThresholds.warning_probability || 0.6,
        advisory_probability: editedThresholds.advisory_probability || 0.3,
      };

      const response = await fetch('/api/thresholds', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(thresholdData),
      });

      if (!response.ok) throw new Error('Failed to update thresholds');

      const data = await response.json();

      toast({
        title: 'Success',
        description: 'Threshold configuration updated successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update thresholds',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Configuration</h1>
          <p className="text-gray-900">
            Administrator settings for resources, thresholds, and zone parameters
          </p>
        </div>
        <Button onClick={fetchConfigData} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="resources" className="space-y-4">
        <TabsList>
          <TabsTrigger value="resources">
            <Settings className="h-4 w-4 mr-2" />
            Resource Capacities
          </TabsTrigger>
          <TabsTrigger value="thresholds">
            <AlertTriangle className="h-4 w-4 mr-2" />
            River Thresholds
          </TabsTrigger>
          <TabsTrigger value="zones">
            <AlertCircle className="h-4 w-4 mr-2" />
            Zone Parameters
          </TabsTrigger>
        </TabsList>

        {/* Resource Capacities Tab */}
        <TabsContent value="resources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Resource Capacity Configuration</CardTitle>
              <CardDescription>
                Set the available capacity for each resource type used in flood response
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {resources.map(resource => (
                  <div key={resource.resource_id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start space-x-3">
                      <span className="text-3xl">{resource.icon}</span>
                      <div className="flex-1">
                        <Label htmlFor={`capacity-${resource.resource_id}`} className="font-semibold">
                          {resource.name}
                        </Label>
                        <p className="text-xs text-gray-700 mt-1">
                          {resource.description}
                        </p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`capacity-${resource.resource_id}`} className="text-xs">
                        Available Units
                      </Label>
                      <Input
                        id={`capacity-${resource.resource_id}`}
                        type="number"
                        min="0"
                        value={editedCapacities[resource.resource_id] || 0}
                        onChange={(e) => handleCapacityChange(resource.resource_id, e.target.value)}
                        className="w-full"
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 flex justify-end">
                <Button onClick={saveResourceCapacities} disabled={saving}>
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Capacities'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* River Thresholds Tab */}
        <TabsContent value="thresholds" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>River Level Thresholds</CardTitle>
              <CardDescription>
                Configure flood risk thresholds for river levels and probabilities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-4">River Level Thresholds</h4>
                  <div className="space-y-4">
                    {thresholds.filter(t => t.unit === 'ft').map(threshold => (
                      <div key={threshold.id} className="space-y-2">
                        <Label htmlFor={`threshold-${threshold.id}`} className="font-medium">
                          {threshold.name}
                        </Label>
                        <div className="flex items-center space-x-2">
                          <Input
                            id={`threshold-${threshold.id}`}
                            type="number"
                            step="0.1"
                            value={editedThresholds[threshold.id] || 0}
                            onChange={(e) => handleThresholdChange(threshold.id, e.target.value)}
                            className="w-24"
                          />
                          <span className="text-sm text-gray-700">{threshold.unit}</span>
                        </div>
                        <p className="text-xs text-gray-700">{threshold.description}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-4">Probability Thresholds</h4>
                  <div className="space-y-4">
                    {thresholds.filter(t => t.unit === '%').map(threshold => (
                      <div key={threshold.id} className="space-y-2">
                        <Label htmlFor={`threshold-${threshold.id}`} className="font-medium">
                          {threshold.name}
                        </Label>
                        <div className="flex items-center space-x-2">
                          <Input
                            id={`threshold-${threshold.id}`}
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={editedThresholds[threshold.id] || 0}
                            onChange={(e) => handleThresholdChange(threshold.id, e.target.value)}
                            className="w-24"
                          />
                          <span className="text-sm text-gray-700">
                            {((editedThresholds[threshold.id] || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-700">{threshold.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <Button onClick={saveThresholds} disabled={saving}>
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Thresholds'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Zone Parameters Tab */}
        <TabsContent value="zones" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Zone Vulnerability Parameters</CardTitle>
              <CardDescription>
                Configure parameters that affect zone vulnerability scoring and resource allocation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 text-left font-semibold">Zone</th>
                      <th className="py-2 text-left font-semibold">River Proximity</th>
                      <th className="py-2 text-left font-semibold">Elevation Risk</th>
                      <th className="py-2 text-left font-semibold">Population Density</th>
                      <th className="py-2 text-left font-semibold">Critical Infrastructure</th>
                      <th className="py-2 text-left font-semibold">Hospital Count</th>
                      <th className="py-2 text-left font-semibold">Critical Infra</th>
                    </tr>
                  </thead>
                  <tbody>
                    {zones.map((zone) => (
                      <tr key={zone.zone_id} className="border-b">
                        <td className="py-3 pr-3">
                          <div className="font-semibold">{zone.name}</div>
                          <div className="text-xs text-gray-700">{zone.zone_id}</div>
                        </td>
                        <td className="py-3 pr-3">
                          <Input
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={editedZones[zone.zone_id]?.river_proximity || 0}
                            onChange={(e) => handleZoneChange(zone.zone_id, 'river_proximity', e.target.value)}
                            className="w-20"
                          />
                        </td>
                        <td className="py-3 pr-3">
                          <Input
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={editedZones[zone.zone_id]?.elevation_risk || 0}
                            onChange={(e) => handleZoneChange(zone.zone_id, 'elevation_risk', e.target.value)}
                            className="w-20"
                          />
                        </td>
                        <td className="py-3 pr-3">
                          <Input
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={editedZones[zone.zone_id]?.pop_density || 0}
                            onChange={(e) => handleZoneChange(zone.zone_id, 'pop_density', e.target.value)}
                            className="w-20"
                          />
                        </td>
                        <td className="py-3 pr-3">
                          <Input
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={editedZones[zone.zone_id]?.crit_infra_score || 0}
                            onChange={(e) => handleZoneChange(zone.zone_id, 'crit_infra_score', e.target.value)}
                            className="w-20"
                          />
                        </td>
                        <td className="py-3 pr-3">
                          <Input
                            type="number"
                            min="0"
                            value={editedZones[zone.zone_id]?.hospital_count || 0}
                            onChange={(e) => handleZoneChange(zone.zone_id, 'hospital_count', e.target.value)}
                            className="w-20"
                          />
                        </td>
                        <td className="py-3 pr-3">
                          <input
                            type="checkbox"
                            checked={editedZones[zone.zone_id]?.critical_infra || false}
                            onChange={(e) => handleZoneChange(zone.zone_id, 'critical_infra', e.target.checked)}
                            className="w-4 h-4"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-6 flex justify-end">
                <Button onClick={saveZoneParameters} disabled={saving}>
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Zone Parameters'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}