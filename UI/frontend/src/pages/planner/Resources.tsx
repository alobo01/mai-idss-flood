import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, Save, RefreshCw, Settings, BarChart3, AlertCircle, CheckCircle2, Info } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ResourceType {
  resource_id: string;
  name: string;
  description: string;
  icon: string;
  display_order: number;
  capacity: number;
}

interface ZoneAllocation {
  zone_id: string;
  zone_name: string;
  units_allocated: number;
  resource_units: Record<string, number>;
  resource_scores?: Record<string, number>;
  satisfaction_level?: number;
  priority_index: number;
  impact_level: string;
  pf?: number;
  vulnerability?: number;
  is_critical_infra?: boolean;
}

interface DispatchResult {
  mode: string;
  use_optimizer: boolean;
  fairness_level?: number;
  global_flood_probability: number;
  resource_summary: {
    total_allocated_units: number;
    per_resource_type: Record<string, number>;
    available_capacity?: Record<string, number>;
  };
  zones: ZoneAllocation[];
  resource_metadata: Record<string, ResourceType>;
}

// Helper function to generate rule explanation based on antecedents
function getRuleExplanation(zone: ZoneAllocation): { title: string; details: string[] } {
  const pf = zone.pf ?? 0;
  const vulnerability = zone.vulnerability ?? 0;
  const iz = pf * vulnerability; // Impact zone (flood probability × vulnerability)
  const isCriticalInfra = zone.is_critical_infra ?? false;
  const impact = zone.impact_level;

  const details: string[] = [];
  
  // Antecedent 1: Flood probability
  details.push(`Flood probability (PF): ${(pf * 100).toFixed(1)}%`);
  
  // Antecedent 2: Vulnerability
  details.push(`Zone vulnerability: ${vulnerability.toFixed(2)}`);
  
  // Derived impact zone
  details.push(`Impact zone (PF × Vulnerability): ${iz.toFixed(3)}`);
  
  // Antecedent 3: Critical infrastructure status
  if (isCriticalInfra) {
    details.push(`⚠️ Critical infrastructure present (+10% allocation boost)`);
  }
  
  // Rule classification
  let ruleTitle = '';
  if (iz < 0.3) {
    ruleTitle = 'Rule: NORMAL (IZ < 0.3) → 0% base allocation';
  } else if (iz < 0.6) {
    ruleTitle = 'Rule: ADVISORY (0.3 ≤ IZ < 0.6) → 10% base allocation';
  } else if (iz < 0.8) {
    ruleTitle = 'Rule: WARNING (0.6 ≤ IZ < 0.8) → 30% base allocation';
  } else {
    const criticalBonus = isCriticalInfra ? ' + 10% critical infra bonus' : '';
    ruleTitle = `Rule: CRITICAL (IZ ≥ 0.8) → ${isCriticalInfra ? '60%' : '50%'} base allocation${criticalBonus}`;
  }
  
  return {
    title: ruleTitle,
    details
  };
}

export function ResourcesPage() {
  const [resources, setResources] = useState<ResourceType[]>([]);
  const [heuristicResult, setHeuristicResult] = useState<DispatchResult | null>(null);
  const [optimizedResult, setOptimizedResult] = useState<DispatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editedCapacities, setEditedCapacities] = useState<Record<string, number>>({});
  const { toast } = useToast();

  // Fetch resource types
  const fetchResources = async () => {
    try {
      const response = await fetch('/api/resource-types');
      const data = await response.json();
      setResources(data.rows);
      
      // Initialize edited capacities
      const capacities: Record<string, number> = {};
      data.rows.forEach((r: ResourceType) => {
        capacities[r.resource_id] = r.capacity;
      });
      setEditedCapacities(capacities);
    } catch (error) {
      console.error('Failed to fetch resources:', error);
      toast({
        title: 'Error',
        description: 'Failed to load resource types',
        variant: 'destructive',
      });
    }
  };

  // Fetch allocations
  const fetchAllocations = async () => {
    setLoading(true);
    try {
      // Fetch heuristic allocation
      const heuristicRes = await fetch('/api/rule-based/dispatch?total_units=100&mode=fuzzy&lead_time=1');
      const heuristicData = await heuristicRes.json();
      setHeuristicResult(heuristicData);

      // Fetch optimized allocation
      const optimizedRes = await fetch('/api/rule-based/dispatch?use_optimizer=true&lead_time=1');
      const optimizedData = await optimizedRes.json();
      setOptimizedResult(optimizedData);
    } catch (error) {
      console.error('Failed to fetch allocations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load resource allocations',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
    fetchAllocations();
  }, []);

  const handleCapacityChange = (resourceId: string, value: string) => {
    const numValue = parseInt(value) || 0;
    setEditedCapacities(prev => ({ ...prev, [resourceId]: numValue }));
  };

  const handleSaveCapacities = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/resource-types/capacities', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          capacities: editedCapacities
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update capacities');
      }

      const data = await response.json();
      
      // Update local state with response
      setResources(data.resources);

      toast({
        title: 'Success',
        description: `Updated ${data.updated_count} resource capacities`,
      });

      // Refresh allocations
      fetchAllocations();
    } catch (error) {
      console.error('Failed to save capacities:', error);
      toast({
        title: 'Error',
        description: 'Failed to update resource capacities',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'text-red-600 bg-red-50';
      case 'WARNING': return 'text-orange-600 bg-orange-50';
      case 'ADVISORY': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-green-600 bg-green-50';
    }
  };

  const checkResourceShortage = (zone: ZoneAllocation, result: DispatchResult) => {
    const shortages: string[] = [];
    
    // Only show warnings when:
    // 1. Fuzzy system determined resource is necessary (resource_scores > 0)
    // 2. AND satisfaction level < 1.0 (not fully satisfied)
    // 3. AND allocated amount is 0 (missing resource)
    if (!zone.resource_scores || zone.satisfaction_level === undefined || zone.satisfaction_level >= 0.99) {
      return shortages;
    }
    
    Object.entries(zone.resource_scores).forEach(([resourceId, score]) => {
      if (score > 0.05) {  // Fuzzy system says this resource is necessary
        const allocated = zone.resource_units[resourceId] || 0;
        if (allocated === 0 && result.resource_metadata[resourceId]) {
          shortages.push(result.resource_metadata[resourceId].name);
        }
      }
    });
    return shortages;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Resource Management</h1>
          <p className="text-muted-foreground">
            Manage resource capacities and view allocation strategies
          </p>
        </div>
        <Button onClick={fetchAllocations} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="capacity" className="space-y-4">
        <TabsList>
          <TabsTrigger value="capacity">
            <Settings className="h-4 w-4 mr-2" />
            Capacity Settings
          </TabsTrigger>
          <TabsTrigger value="heuristic">
            <BarChart3 className="h-4 w-4 mr-2" />
            Heuristic Allocation
          </TabsTrigger>
          <TabsTrigger value="optimized">
            <BarChart3 className="h-4 w-4 mr-2" />
            Optimized Allocation
          </TabsTrigger>
        </TabsList>

        {/* Capacity Settings Tab */}
        <TabsContent value="capacity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Resource Capacity Configuration</CardTitle>
              <CardDescription>
                Set the available capacity for each resource type
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
                        <p className="text-xs text-muted-foreground mt-1">
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
                <Button onClick={handleSaveCapacities} disabled={saving}>
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Capacities'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Heuristic Allocation Tab */}
        <TabsContent value="heuristic" className="space-y-4">
          {heuristicResult && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Heuristic Allocation Summary</CardTitle>
                  <CardDescription>
                    Fuzzy logic-based allocation (100 total units)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div>
                      <p className="text-sm text-muted-foreground">Mode</p>
                      <p className="text-2xl font-bold capitalize">{heuristicResult.mode}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Units</p>
                      <p className="text-2xl font-bold">{heuristicResult.resource_summary.total_allocated_units}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Zones</p>
                      <p className="text-2xl font-bold">{heuristicResult.zones.length}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Flood Probability</p>
                      <p className="text-2xl font-bold">{(heuristicResult.global_flood_probability * 100).toFixed(0)}%</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-semibold">Resource Distribution</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                      {Object.entries(heuristicResult.resource_summary.per_resource_type).map(([resourceId, count]) => {
                        const meta = heuristicResult.resource_metadata[resourceId];
                        return (
                          <div key={resourceId} className="border rounded p-3">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="text-2xl">{meta.icon}</span>
                              <span className="text-sm font-medium">{meta.name}</span>
                            </div>
                            <p className="text-2xl font-bold">{count} units</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Zone Allocations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {heuristicResult.zones.map(zone => {
                      const explanation = getRuleExplanation(zone);
                      return (
                        <div key={zone.zone_id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h4 className="font-semibold">{zone.zone_name}</h4>
                              <Badge className={getImpactColor(zone.impact_level)}>
                                {zone.impact_level}
                              </Badge>
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold">{zone.units_allocated}</p>
                              <p className="text-xs text-muted-foreground">units allocated</p>
                            </div>
                          </div>
                          
                          {/* Rule Explanation */}
                          <div className="mb-3 p-3 bg-muted/50 rounded-md border border-muted">
                            <div className="flex items-start space-x-2">
                              <Info className="h-4 w-4 mt-0.5 text-blue-600 flex-shrink-0" />
                              <div className="text-sm space-y-1">
                                <p className="font-semibold text-blue-900 dark:text-blue-100">{explanation.title}</p>
                                <div className="text-muted-foreground space-y-0.5">
                                  {explanation.details.map((detail, idx) => (
                                    <p key={idx} className="text-xs leading-relaxed">{detail}</p>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-3 md:grid-cols-7 gap-2">
                            {resources.map(resource => {
                              const allocated = zone.resource_units[resource.resource_id] || 0;
                              return (
                                <div key={resource.resource_id} className="text-center border rounded p-2">
                                  <div className="text-xl">{resource.icon}</div>
                                  <div className="text-lg font-semibold">{allocated}</div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Optimized Allocation Tab */}
        <TabsContent value="optimized" className="space-y-4">
          {optimizedResult && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Optimized Fair Allocation Summary</CardTitle>
                  <CardDescription>
                    Linear programming with max-min fairness objective
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                    <div>
                      <p className="text-sm text-muted-foreground">Optimizer</p>
                      <p className="text-2xl font-bold">{optimizedResult.use_optimizer ? 'Active' : 'Disabled'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Fairness Level</p>
                      <p className="text-2xl font-bold">{((optimizedResult.fairness_level || 0) * 100).toFixed(0)}%</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Units</p>
                      <p className="text-2xl font-bold">{optimizedResult.resource_summary.total_allocated_units}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Zones</p>
                      <p className="text-2xl font-bold">{optimizedResult.zones.length}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Flood Probability</p>
                      <p className="text-2xl font-bold">{(optimizedResult.global_flood_probability * 100).toFixed(0)}%</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-semibold">Resource Utilization</h4>
                    <div className="space-y-3">
                      {Object.entries(optimizedResult.resource_summary.per_resource_type).map(([resourceId, allocated]) => {
                        const meta = optimizedResult.resource_metadata[resourceId];
                        const capacity = optimizedResult.resource_summary.available_capacity?.[resourceId] || 0;
                        const percentage = capacity > 0 ? (allocated / capacity) * 100 : 0;
                        return (
                          <div key={resourceId} className="space-y-2">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <span className="text-xl">{meta.icon}</span>
                                <span className="text-sm font-medium">{meta.name}</span>
                              </div>
                              <span className="text-sm font-semibold">
                                {allocated} / {capacity} units ({percentage.toFixed(0)}%)
                              </span>
                            </div>
                            <Progress value={percentage} className="h-2" />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Zone Allocations with Warnings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {optimizedResult.zones.map(zone => {
                      const shortages = checkResourceShortage(zone, optimizedResult);
                      const hasShortages = shortages.length > 0;
                      return (
                        <div key={zone.zone_id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <h4 className="font-semibold">{zone.zone_name}</h4>
                                {hasShortages && (
                                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                                )}
                              </div>
                              <div className="flex items-center space-x-2">
                                <Badge className={getImpactColor(zone.impact_level)}>
                                  {zone.impact_level}
                                </Badge>
                                {zone.satisfaction_level !== undefined && (
                                  <Badge variant="outline" className="flex items-center space-x-1">
                                    {zone.satisfaction_level >= 0.99 ? (
                                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                                    ) : (
                                      <AlertCircle className="h-3 w-3 text-orange-500" />
                                    )}
                                    <span>{(zone.satisfaction_level * 100).toFixed(0)}% satisfied</span>
                                  </Badge>
                                )}
                              </div>
                              {hasShortages && (
                                <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-700">
                                  <strong>⚠️ Missing resources:</strong> {shortages.join(', ')}
                                </div>
                              )}
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold">{zone.units_allocated}</p>
                              <p className="text-xs text-muted-foreground">units allocated</p>
                            </div>
                          </div>
                          <div className="grid grid-cols-3 md:grid-cols-7 gap-2">
                            {resources.map(resource => {
                              const allocated = zone.resource_units[resource.resource_id] || 0;
                              const isMissing = allocated === 0 && shortages.includes(resource.name);
                              return (
                                <div 
                                  key={resource.resource_id} 
                                  className={`text-center border rounded p-2 ${isMissing ? 'bg-orange-50 border-orange-300' : ''}`}
                                >
                                  <div className="text-xl">{resource.icon}</div>
                                  <div className={`text-lg font-semibold ${allocated === 0 ? 'text-muted-foreground' : ''}`}>
                                    {allocated}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
