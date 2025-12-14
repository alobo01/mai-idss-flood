import React, { useMemo, useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, RefreshCw, AlertCircle, CheckCircle2, Info } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAppContext } from '@/contexts/AppContext';
import { RULE_SCENARIO_LABELS } from '@/types';

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
  lead_time_days?: number;
  mode: string;
  use_optimizer: boolean;
  fuzzy_engine_available?: boolean;
  fairness_level?: number;
  global_flood_probability: number;
  total_units?: number;
  last_prediction?: {
    forecast_date?: string;
    date?: string;
    predicted_level?: number;
    lower_bound_80?: number;
    upper_bound_80?: number;
    flood_probability?: number;
    days_ahead?: number;
    created_at?: string;
  };
  resource_summary: {
    total_allocated_units: number;
    per_resource_type: Record<string, number>;
    available_capacity?: Record<string, number>;
  };
  zones: ZoneAllocation[];
  resource_metadata: Record<string, ResourceType>;
}

const IMPACT_ORDER: Record<string, number> = {
  CRITICAL: 0,
  WARNING: 1,
  ADVISORY: 2,
  NORMAL: 3,
};

function formatPct(value?: number) {
  if (value === undefined || Number.isNaN(value)) return '—';
  return `${(value * 100).toFixed(0)}%`;
}

function formatIsoDate(value?: string) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
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

interface ResourcesPageProps {
  selectedDate?: string;
}

export function ResourcesPage({ selectedDate }: ResourcesPageProps) {
  const [optimizedResult, setOptimizedResult] = useState<DispatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const { leadTimeDays, setLeadTimeDays, scenario } = useAppContext();
  const [zoneQuery, setZoneQuery] = useState('');
  const [onlyShortages, setOnlyShortages] = useState(false);
  const { toast } = useToast();

  
  // Fetch allocations
  const fetchAllocations = async () => {
    setLoading(true);
    try {
      // Fetch optimized allocation (use selected lead time)
      const optimizedParams = new URLSearchParams({
        total_units: '100',
        mode: 'fuzzy',
        lead_time: String(leadTimeDays),
        scenario,
        use_optimizer: 'true',
        ...(selectedDate && { as_of_date: selectedDate }),
      });
      const optimizedRes = await fetch(`/api/rule-based/dispatch?${optimizedParams.toString()}`);
      if (!optimizedRes.ok) {
        const body = await optimizedRes.text();
        throw new Error(`Optimized dispatch failed (HTTP ${optimizedRes.status}): ${body}`);
      }
      setOptimizedResult(await optimizedRes.json());
    } catch (error) {
      console.error('Failed to fetch allocations:', error);
      setOptimizedResult(null);
      toast({
        title: 'Error',
        description: 'Failed to load resource allocations',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch allocations when lead time, scenario, or selected date changes
  useEffect(() => {
    fetchAllocations();
  }, [leadTimeDays, scenario, selectedDate]);

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
    
    Object.entries(zone.resource_scores || {}).forEach(([resourceId, score]) => {
      if (score > 0.05) {  // Fuzzy system says this resource is necessary
        const allocated = zone.resource_units[resourceId] || 0;
        if (allocated === 0 && result.resource_metadata[resourceId]) {
          shortages.push(result.resource_metadata[resourceId].name);
        }
      }
    });
    return shortages;
  };

  const getZoneRows = (result: DispatchResult | null) => {
    const query = zoneQuery.trim().toLowerCase();
    const zones = (result?.zones || []).filter((z) => {
      if (!query) return true;
      return `${z.zone_name} ${z.zone_id}`.toLowerCase().includes(query);
    });

    const withShortages =
      onlyShortages && result
        ? zones.filter((z) => checkResourceShortage(z, result).length > 0)
        : zones;

    return withShortages.sort((a, b) => {
      const impactA = IMPACT_ORDER[a.impact_level] ?? 999;
      const impactB = IMPACT_ORDER[b.impact_level] ?? 999;
      if (impactA !== impactB) return impactA - impactB;
      return (b.units_allocated || 0) - (a.units_allocated || 0);
    });
  };

  const renderZoneResources = (
    zone: ZoneAllocation,
    meta: Record<string, ResourceType>,
    options?: { maxItems?: number },
  ) => {
    const entries = Object.entries(zone.resource_units || {})
      .filter(([, value]) => (value || 0) > 0)
      .sort((a, b) => (b[1] || 0) - (a[1] || 0));

    if (entries.length === 0) return <span className="text-muted-foreground">—</span>;

    const maxItems = options?.maxItems;
    const shown = maxItems ? entries.slice(0, maxItems) : entries;
    const remaining = maxItems ? entries.length - shown.length : 0;

    return (
      <div className="flex flex-wrap gap-1">
        {shown.map(([resourceId, value]) => {
          const r = meta[resourceId];
          return (
            <span
              key={resourceId}
              className="inline-flex items-center gap-1 rounded border bg-background px-2 py-0.5 text-xs"
              title={r?.name || resourceId}
            >
              <span className="text-base leading-none">{r?.icon || '•'}</span>
              <span className="font-semibold">{value}</span>
            </span>
          );
        })}
        {remaining > 0 && (
          <span className="inline-flex items-center rounded border bg-background px-2 py-0.5 text-xs text-muted-foreground">
            +{remaining}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Resource Allocation</h1>
          <p className="text-muted-foreground">
            View optimized resource allocation and capacity utilization
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <Label className="text-sm">Lead time (days)</Label>
            <select
              value={leadTimeDays}
              onChange={(e) => setLeadTimeDays(parseInt(e.target.value))}
              className="border rounded px-2 py-1 bg-white text-gray-900 border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </div>
          <div className="text-xs text-muted-foreground">
            Scenario: <span className="font-semibold text-foreground">{RULE_SCENARIO_LABELS[scenario]}</span>
          </div>
          <Button onClick={fetchAllocations} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        {/* Optimized Allocation */}
          {optimizedResult && (
            <>
              {/* Capacity Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>Capacity Overview</CardTitle>
                  <CardDescription>
                    Comparison of actual available capacity vs. needed capacity by optimized allocation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(optimizedResult?.resource_summary?.per_resource_type || {}).map(([resourceId, allocated]) => {
                      const meta = optimizedResult.resource_metadata[resourceId];
                      if (!meta) return null;
                      const capacity = optimizedResult.resource_summary.available_capacity?.[resourceId] || 0;
                      const shortage = Math.max(0, allocated - capacity);
                      const surplus = Math.max(0, capacity - allocated);
                      const utilizationPercentage = capacity > 0 ? (allocated / capacity) * 100 : 0;
                      const hasShortage = shortage > 0;

                      return (
                        <div key={resourceId} className={`border rounded-lg p-4 ${hasShortage ? 'border-red-300 bg-red-100' : ''}`}>
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-2">
                              <span className="text-2xl">{meta.icon}</span>
                              <span className={`font-semibold text-sm ${hasShortage ? 'text-red-900' : ''}`}>{meta.name}</span>
                            </div>
                            {hasShortage && (
                              <Badge variant="destructive" className="text-xs">
                                Shortage
                              </Badge>
                            )}
                          </div>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className={`text-muted-foreground ${hasShortage ? 'text-red-700' : ''}`}>Available:</span>
                              <span className={`font-semibold ${hasShortage ? 'text-red-900' : ''}`}>{capacity} units</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className={`text-muted-foreground ${hasShortage ? 'text-red-700' : ''}`}>Needed:</span>
                              <span className={`font-semibold ${hasShortage ? 'text-red-900' : ''}`}>{allocated} units</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className={`text-muted-foreground ${hasShortage ? 'text-red-700' : ''}`}>
                                {hasShortage ? 'Shortage:' : surplus > 0 ? 'Surplus:' : 'Utilization:'}
                              </span>
                              <span className={`font-semibold ${hasShortage ? 'text-red-900 font-bold' : surplus > 0 ? 'text-green-600' : 'text-blue-600'}`}>
                                {hasShortage ? `-${shortage}` : surplus > 0 ? `+${surplus}` : `${utilizationPercentage.toFixed(0)}%`}
                              </span>
                            </div>
                            <Progress
                              value={Math.min(100, utilizationPercentage)}
                              className={`h-2 ${hasShortage ? 'bg-red-200' : ''}`}
                            />
                          </div>
                        </div>
                      );
                    })}
                    {/* If no resources allocated */}
                    {Object.keys(optimizedResult?.resource_summary?.per_resource_type || {}).length === 0 && (
                      <div className="col-span-full text-center text-muted-foreground py-8">
                        No resource allocations to display
                      </div>
                    )}
                  </div>
                  {Object.entries(optimizedResult?.resource_summary?.per_resource_type || {}).some(([resourceId, allocated]) => {
                    const capacity = optimizedResult.resource_summary.available_capacity?.[resourceId] || 0;
                    return allocated > capacity;
                  }) && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                      <div className="flex items-center gap-2 text-red-700">
                        <AlertTriangle className="h-4 w-4" />
                        <span className="text-sm font-medium">
                          Resource shortages detected - some allocations exceed available capacity
                        </span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

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
                      <p className="text-2xl font-bold">
                        {optimizedResult.fairness_level === undefined || optimizedResult.fairness_level === null
                          ? '—'
                          : formatPct(optimizedResult.fairness_level)}
                      </p>
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
                      <p className="text-2xl font-bold">{formatPct(optimizedResult.global_flood_probability)}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-semibold">Resource Utilization</h4>
                    <div className="space-y-3">
                      {Object.entries(optimizedResult?.resource_summary?.per_resource_type || {}).map(([resourceId, allocated]) => {
                        const meta = optimizedResult.resource_metadata[resourceId];
                        if (!meta) return null;
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
                  <CardDescription>
                    Filter and scan shortages quickly (expand a row for full resource breakdown)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div className="flex-1">
                      <Label className="text-xs text-muted-foreground">Search zones</Label>
                      <Input
                        value={zoneQuery}
                        onChange={(e) => setZoneQuery(e.target.value)}
                        placeholder="e.g. South Riverfront or Z1S"
                        className="mt-1"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-2 text-xs text-muted-foreground">
                        <input
                          type="checkbox"
                          checked={onlyShortages}
                          onChange={(e) => setOnlyShortages(e.target.checked)}
                        />
                        Only shortages
                      </label>
                      <div className="text-xs text-muted-foreground">
                        Showing{' '}
                        <span className="font-semibold text-foreground">{getZoneRows(optimizedResult).length}</span> /{' '}
                        <span className="font-semibold text-foreground">{optimizedResult.zones.length}</span> zones
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="py-2 text-left font-semibold">Zone</th>
                          <th className="py-2 text-left font-semibold">Impact</th>
                          <th className="py-2 text-right font-semibold">Units</th>
                          <th className="py-2 text-left font-semibold">Satisfaction</th>
                          <th className="py-2 text-left font-semibold">Shortages</th>
                          <th className="py-2 text-left font-semibold">Resources</th>
                        </tr>
                      </thead>
                      <tbody>
                        {getZoneRows(optimizedResult).map((zone) => {
                          const shortages = checkResourceShortage(zone, optimizedResult);
                          const hasShortages = shortages.length > 0;
                          const satisfaction = zone.satisfaction_level;
                          return (
                            <tr key={zone.zone_id} className="border-b align-top">
                              <td className="py-3 pr-3">
                                <div className="flex items-center gap-2">
                                  <div className="font-semibold">{zone.zone_name}</div>
                                  {hasShortages && <AlertTriangle className="h-4 w-4 text-orange-500" />}
                                </div>
                                <div className="text-xs text-muted-foreground">{zone.zone_id}</div>
                              </td>
                              <td className="py-3 pr-3">
                                <Badge className={getImpactColor(zone.impact_level)}>{zone.impact_level}</Badge>
                              </td>
                              <td className="py-3 pr-3 text-right">
                                <div className="text-lg font-bold leading-none">{zone.units_allocated}</div>
                                <div className="text-xs text-muted-foreground">units</div>
                              </td>
                              <td className="py-3 pr-3">
                                {satisfaction === undefined ? (
                                  <span className="text-muted-foreground">—</span>
                                ) : (
                                  <div className="min-w-[10rem] space-y-1">
                                    <div className="flex items-center gap-2 text-xs">
                                      {satisfaction >= 0.99 ? (
                                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                                      ) : (
                                        <AlertCircle className="h-4 w-4 text-orange-500" />
                                      )}
                                      <span className="font-semibold">{formatPct(satisfaction)}</span>
                                    </div>
                                    <Progress value={Math.max(0, Math.min(100, satisfaction * 100))} className="h-2" />
                                  </div>
                                )}
                              </td>
                              <td className="py-3 pr-3">
                                {hasShortages ? (
                                  <div className="space-y-1">
                                    <div className="inline-flex items-center gap-1 rounded border border-orange-200 bg-orange-50 px-2 py-0.5 text-xs text-orange-700">
                                      <AlertTriangle className="h-3.5 w-3.5" />
                                      Missing {shortages.length}
                                    </div>
                                    <div className="text-xs text-muted-foreground">{shortages.join(', ')}</div>
                                  </div>
                                ) : (
                                  <span className="text-muted-foreground">—</span>
                                )}
                              </td>
                              <td className="py-3">
                                <details className="rounded-md border bg-muted/20 px-3 py-2">
                                  <summary className="cursor-pointer select-none text-xs font-semibold">
                                    View breakdown
                                  </summary>
                                  <div className="mt-2">{renderZoneResources(zone, optimizedResult.resource_metadata)}</div>
                                </details>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
    </div>
    </div>
  );
}
