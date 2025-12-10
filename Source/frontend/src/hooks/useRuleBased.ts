import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { buildApiUrl } from '@/lib/apiBase';

// Types for rule-based responses
export interface AnalyzedZone {
  zone_id: string;
  zone_name: string;
  priority_score: number;
  priority_level: 'low' | 'medium' | 'high' | 'critical';
  population: number;
  area_km2: number;
  population_density: number;
  critical_assets_count: number;
  critical_assets: string[];
  recommended_resources: {
    [resourceType: string]: number;
  };
  estimated_response_time_minutes: number;
  risk_factors: {
    active_alerts: number;
    alert_severity: string;
    risk_multiplier: number;
    density_factor: number;
  };
  geometry?: string; // GeoJSON string
  last_updated: string;
}

export interface ZoneAllocation {
  zone_id: string;
  zone_name: string;
  resources_allocated: {
    [resourceType: string]: number;
  };
  allocation_timestamp: string;
  estimated_effectiveness: number;
}

export interface RuleBasedAllocation {
  incident_type: string;
  allocation_timestamp: string;
  zones: ZoneAllocation[];
  total_resources_allocated: {
    [resourceType: string]: number;
  };
  allocation_efficiency: number;
  unmet_needs: Array<{
    zone_id: string;
    zone_name: string;
    resource_type: string;
    required: number;
    allocated: number;
    shortage: number;
  }>;
  constraints_applied?: {
    [key: string]: any;
  };
}

export type RuleEngineMode = 'crisp' | 'fuzzy' | 'proportional';

export interface PipelineRuleBasedAllocation {
  zone_id: string;
  zone_name: string;
  impact_level: string;
  allocation_mode: string;
  units_allocated: number;
  pf?: number;
  vulnerability?: number;
  iz?: number;
}

export interface PipelineRuleBasedResponse {
  global_pf: number;
  mode: RuleEngineMode;
  total_units: number;
  max_units_per_zone: number;
  allocations: PipelineRuleBasedAllocation[];
  total_allocated?: number;
  updated_at?: string;
}

// Generic fetch function
const fetchFromApi = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(buildApiUrl(endpoint), options);

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

// Hook for getting rule-based zone analysis
export const useRuleBasedZones = (
  minPopulation?: number,
  maxPopulation?: number,
  riskLevel?: 'low' | 'moderate' | 'high' | 'severe'
) => {
  const params = new URLSearchParams();
  if (minPopulation !== undefined) params.append('min_population', minPopulation.toString());
  if (maxPopulation !== undefined) params.append('max_population', maxPopulation.toString());
  if (riskLevel) params.append('risk_level', riskLevel);

  return useQuery({
    queryKey: ['rule-based-zones', minPopulation, maxPopulation, riskLevel],
    queryFn: () => fetchFromApi<AnalyzedZone[]>(`/rule-based/zones?${params}`),
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 10, // Refresh every 10 minutes
  });
};

// Hook for rule-based resource allocation
export const useRuleBasedAllocation = () => {
  const queryClient = useQueryClient();

  const allocateResources = useMutation({
    mutationFn: async (request: {
      incident_type?: string;
      available_resources?: {
        [resourceType: string]: {
          count: number;
          capacity?: number;
        };
      };
      zone_priorities?: {
        [zoneId: string]: number;
      };
      zone_ids?: string[];
      constraints?: {
        [key: string]: any;
      };
    }) => {
      return fetchFromApi<RuleBasedAllocation>('/rule-based/allocate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['rule-based-zones'] });
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });

  return allocateResources;
};

// Hook for pipeline-style rule-based allocation (Models/rule_based.py)
export const useRuleBasedPipeline = ({
  globalPf = 0.55,
  totalUnits = 12,
  mode = 'crisp',
  maxUnitsPerZone = 6,
  enabled = true,
}: {
  globalPf?: number;
  totalUnits?: number;
  mode?: RuleEngineMode;
  maxUnitsPerZone?: number;
  enabled?: boolean;
}) => {
  return useQuery({
    queryKey: ['rule-based-pipeline', globalPf, totalUnits, mode, maxUnitsPerZone],
    enabled,
    queryFn: () => {
      const params = new URLSearchParams({
        global_pf: String(globalPf),
        total_units: String(totalUnits),
        mode,
        max_units_per_zone: String(maxUnitsPerZone),
      });

      return fetchFromApi<PipelineRuleBasedResponse>(`/rule-based/pipeline?${params.toString()}`);
    },
    staleTime: 1000 * 60 * 3,
  });
};
