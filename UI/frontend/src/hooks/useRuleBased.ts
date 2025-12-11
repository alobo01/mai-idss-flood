import { PipelineRuleBasedAllocation } from '../types';
import { mockRulePipeline } from '../lib/mockData';

export type { PipelineRuleBasedAllocation };

export const useRuleBasedPipeline = ({
  globalPf = 0.55,
  totalUnits = 12,
  mode = 'crisp',
  maxUnitsPerZone = 6,
}: {
  globalPf?: number;
  totalUnits?: number;
  mode?: 'crisp' | 'fuzzy' | 'proportional';
  maxUnitsPerZone?: number;
}) => {
  // Return mock data directly
  return {
    data: mockRulePipeline,
    isLoading: false,
    error: null
  };
};