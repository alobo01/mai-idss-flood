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