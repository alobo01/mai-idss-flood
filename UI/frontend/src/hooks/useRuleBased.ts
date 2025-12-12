import React from 'react';
import { PipelineRuleBasedAllocation } from '../types';
import { mockRulePipeline } from '../lib/mockData';

export type { PipelineRuleBasedAllocation };

export const useRuleBasedPipeline = ({
  totalUnits = 12,
  mode = 'fuzzy',
  maxUnitsPerZone = 6,
  leadTime = 1,
}: {
  totalUnits?: number;
  mode?: 'crisp' | 'fuzzy' | 'proportional';
  maxUnitsPerZone?: number;
  leadTime?: number;
}) => {
  const [data, setData] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<any>(null);

  React.useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    setError(null);

    const url = `/api/rule-based/dispatch?total_units=${totalUnits}&mode=${mode}&lead_time=${leadTime}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        return res.json();
      })
      .then((json) => {
        if (!mounted) return;
        setData(json || null);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err.message || err);
        // Fall back to mock so the UI remains functional
        setData(mockRulePipeline as any);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [totalUnits, mode, maxUnitsPerZone, leadTime]);

  return { data, isLoading, error };
};