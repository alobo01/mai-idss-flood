import React, { useMemo, useState } from 'react';
import { AlertTriangle, Gauge, Layers, RefreshCw, Sparkles, Target } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import {
  PipelineRuleBasedAllocation,
  RuleEngineMode,
  useRuleBasedPipeline,
} from '@/hooks/useRuleBased';

const impactBadge = (impact: string) => {
  const normalized = impact.toUpperCase();
  const variantMap: Record<string, string> = {
    CRITICAL: 'destructive',
    WARNING: 'default',
    ADVISORY: 'secondary',
    NORMAL: 'outline',
  };
  return (
    <Badge variant={(variantMap[normalized] as any) || 'outline'}>
      {normalized}
    </Badge>
  );
};

const formatPct = (value?: number) =>
  value === undefined || Number.isNaN(value) ? '—' : `${Math.round(value * 100)}%`;

export function PlannerRuleBased() {
  const [globalPf, setGlobalPf] = useState(0.55);
  const [totalUnits, setTotalUnits] = useState(14);
  const [mode, setMode] = useState<RuleEngineMode>('crisp');
  const [maxUnitsPerZone, setMaxUnitsPerZone] = useState(6);

  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useRuleBasedPipeline({ globalPf, totalUnits, mode, maxUnitsPerZone });

  const allocations = data?.allocations ?? [];

  const summary = useMemo(() => {
    const totalAllocated = allocations.reduce((sum, a) => sum + a.units_allocated, 0);
    const criticalZones = allocations.filter((a) => a.impact_level?.toUpperCase() === 'CRITICAL').length;
    const highZones = allocations.filter((a) => ['CRITICAL', 'WARNING'].includes((a.impact_level || '').toUpperCase())).length;
    return {
      totalAllocated,
      criticalZones,
      highZones,
      coveragePct: allocations.length > 0 ? Math.min(100, Math.round((highZones / allocations.length) * 100)) : 0,
    };
  }, [allocations]);

  const topAllocations: PipelineRuleBasedAllocation[] = useMemo(() => {
    return [...allocations].sort((a, b) => b.units_allocated - a.units_allocated).slice(0, 3);
  }, [allocations]);

  const handleRun = () => {
    refetch();
  };

  const handleNumberChange = (setter: (v: number) => void, fallback: number) =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const next = Number(event.target.value);
      setter(Number.isFinite(next) ? next : fallback);
    };

  const renderTableBody = () => {
    if (isLoading) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="text-center text-muted-foreground">
            Loading rule engine results...
          </TableCell>
        </TableRow>
      );
    }

    if (error) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="text-center text-destructive">
            Unable to run the rule-based allocator. Please try again.
          </TableCell>
        </TableRow>
      );
    }

    if (allocations.length === 0) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="text-center text-muted-foreground">
            No allocations returned. Adjust the parameters and run again.
          </TableCell>
        </TableRow>
      );
    }

    return allocations.map((allocation) => (
      <TableRow key={allocation.zone_id}>
        <TableCell className="font-medium">
          <div className="flex items-center gap-2">
            <span>{allocation.zone_name}</span>
            <Badge variant="outline">{allocation.zone_id}</Badge>
          </div>
        </TableCell>
        <TableCell>{impactBadge(allocation.impact_level)}</TableCell>
        <TableCell>
          <div className="font-semibold">{allocation.units_allocated}</div>
          <div className="text-xs text-muted-foreground">{allocation.allocation_mode}</div>
        </TableCell>
        <TableCell>{formatPct(allocation.pf)}</TableCell>
        <TableCell>{allocation.vulnerability ? allocation.vulnerability.toFixed(2) : '—'}</TableCell>
        <TableCell>{allocation.iz ? allocation.iz.toFixed(2) : '—'}</TableCell>
      </TableRow>
    ));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Rule-Based Allocation</h1>
          <p className="text-muted-foreground">
            Uses the shared logic from <code>Models/rule_based.py</code> to suggest crisp, fuzzy, or proportional deployments.
          </p>
        </div>
        <Badge variant="outline" className="flex items-center gap-1">
          <Layers className="h-4 w-4" />
          <span>{mode.toUpperCase()} mode</span>
        </Badge>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <CardTitle className="flex items-center gap-2">
            <Gauge className="h-5 w-5" />
            Rule Engine Controls
          </CardTitle>
          <Button onClick={handleRun} disabled={isFetching} className="flex items-center gap-2">
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            {isFetching ? 'Running...' : 'Run rule engine'}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <label className="space-y-1 text-sm">
              <span className="text-muted-foreground">Global flood probability</span>
              <Input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={globalPf}
                onChange={handleNumberChange(setGlobalPf, 0.55)}
              />
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-muted-foreground">Total deployable units</span>
              <Input
                type="number"
                min={0}
                value={totalUnits}
                onChange={handleNumberChange(setTotalUnits, 14)}
              />
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-muted-foreground">Allocation mode</span>
              <Select value={mode} onValueChange={(value) => setMode(value as RuleEngineMode)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="crisp">Crisp</SelectItem>
                  <SelectItem value="fuzzy">Fuzzy</SelectItem>
                  <SelectItem value="proportional">Proportional</SelectItem>
                </SelectContent>
              </Select>
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-muted-foreground">Max units per zone</span>
              <Input
                type="number"
                min={1}
                value={maxUnitsPerZone}
                onChange={handleNumberChange(setMaxUnitsPerZone, 6)}
              />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Sparkles className="h-4 w-4" />
              <span>Realtime rule engine powered by shared model logic</span>
            </div>
            {data?.updated_at && (
              <div className="flex items-center gap-1">
                <Target className="h-4 w-4" />
                <span>Updated {new Date(data.updated_at).toLocaleString()}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total units allocated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">{summary.totalAllocated}</div>
              <Badge variant="secondary">/ {totalUnits}</Badge>
            </div>
            <Progress value={Math.min(100, (summary.totalAllocated / Math.max(totalUnits, 1)) * 100)} className="mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">High-priority zones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">{summary.highZones}</div>
              <Badge variant="outline">{summary.coveragePct}% coverage</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Critical or warning impact levels</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Critical zones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold text-red-600">{summary.criticalZones}</div>
              <AlertTriangle className="h-5 w-5 text-red-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">Zones needing immediate response</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Allocation by zone
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Zone</TableHead>
                <TableHead>Impact</TableHead>
                <TableHead>Units</TableHead>
                <TableHead>PF</TableHead>
                <TableHead>Vulnerability</TableHead>
                <TableHead>Impact score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>{renderTableBody()}</TableBody>
          </Table>
        </CardContent>
      </Card>

      {topAllocations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Top priority placements
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {topAllocations.map((item) => (
              <div key={item.zone_id} className="border rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium">{item.zone_name}</div>
                  {impactBadge(item.impact_level)}
                </div>
                <p className="text-sm text-muted-foreground">{item.units_allocated} units allocated</p>
                <div className="mt-2 text-xs text-muted-foreground space-y-1">
                  <div>PF: {formatPct(item.pf)}</div>
                  <div>Vulnerability: {item.vulnerability ? item.vulnerability.toFixed(2) : '—'}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
