import React from 'react';
import { PipelineRuleBasedAllocation, RuleScenario } from '../types';

export type { PipelineRuleBasedAllocation };

const API_URL = import.meta.env.VITE_API_URL || '/api';

type DispatchZone = {
  zone_id: string;
  units_allocated: number;
  impact_level: string;
  allocation_mode: string;
  pf?: number;
  vulnerability?: number;
};

type DispatchPlanResponse = {
  zones?: DispatchZone[];
  global_flood_probability?: number;
  scenario?: RuleScenario;
  last_prediction?: Record<string, any>;
};

export const useRuleBasedPipeline = ({
  totalUnits = 12,
  mode = 'fuzzy',
  maxUnitsPerZone = 6,
  leadTime = 1,
  scenario = 'normal',
}: {
  totalUnits?: number;
  mode?: 'crisp' | 'fuzzy' | 'proportional';
  maxUnitsPerZone?: number;
  leadTime?: number;
  scenario?: RuleScenario;
}) => {
  const [data, setData] = React.useState<{
    allocations: PipelineRuleBasedAllocation[];
    globalProbability?: number | null;
    scenario?: RuleScenario;
    lastPrediction?: Record<string, any>;
  } | null>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<any>(null);

  React.useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    setError(null);

    const qs = new URLSearchParams({
      total_units: String(totalUnits),
      mode,
      lead_time: String(leadTime),
      max_units_per_zone: String(maxUnitsPerZone),
      scenario,
    });
    const url = `${API_URL}/rule-based/dispatch?${qs.toString()}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        return res.json();
      })
      .then((json: DispatchPlanResponse) => {
        if (!mounted) return;
        const zones = Array.isArray(json?.zones) ? json.zones : [];
        const allocations: PipelineRuleBasedAllocation[] = zones.map((z) => ({
          zone_id: z.zone_id,
          units_allocated: z.units_allocated,
          impact_level: z.impact_level,
          allocation_mode: z.allocation_mode,
          pf: z.pf,
          vulnerability: z.vulnerability,
        }));
        setData({
          allocations,
          globalProbability: json.global_flood_probability ?? null,
          scenario: json.scenario,
          lastPrediction: (json.last_prediction ?? null) as Record<string, any> | null,
        });
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err.message || err);
        setData(null);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [totalUnits, mode, maxUnitsPerZone, leadTime, scenario]);

  return { data, isLoading, error };
};
