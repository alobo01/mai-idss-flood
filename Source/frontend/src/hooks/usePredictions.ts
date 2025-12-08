import { useQuery } from '@tanstack/react-query';
import { buildApiUrl } from '@/lib/apiBase';

// Types for prediction responses
export interface RiverLevelPrediction {
  gauge_id: string;
  gauge_name: string;
  river_name?: string;
  prediction_time: string;
  predicted_level: number;
  confidence_level: number;
  risk_level: 'low' | 'moderate' | 'high' | 'severe';
  trend_per_hour: number;
  data_points_used: number;
}

export interface FloodRiskZone {
  zone_id: string;
  zone_name: string;
  risk_level: number;
  risk_category: 'low' | 'moderate' | 'high' | 'severe';
  confidence: number;
  risk_drivers: Array<{
    factor: string;
    contribution: number;
    description: string;
  }>;
  affected_population: number;
  time_horizon_hours: number;
  recommended_actions: string[];
  geometry?: string; // GeoJSON string
}

export interface FloodRiskPrediction {
  zones: FloodRiskZone[];
  metadata: {
    time_horizon: number;
    generated_at: string;
    gauge_count?: number;
    data_quality?: string;
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

// Hook for river level predictions
export const useRiverLevelPredictions = (
  gaugeCode?: string,
  horizon: number = 24
) => {
  const params = new URLSearchParams();
  if (gaugeCode) params.append('gauge_code', gaugeCode);
  params.append('horizon', horizon.toString());

  return useQuery({
    queryKey: ['river-level-predictions', gaugeCode, horizon],
    queryFn: () => fetchFromApi<RiverLevelPrediction[]>(`/predict/river-level?${params}`),
    staleTime: 1000 * 60 * 10, // 10 minutes
    refetchInterval: 1000 * 60 * 30, // Refresh every 30 minutes
    enabled: !!gaugeCode || horizon > 0,
  });
};

// Hook for flood risk predictions
export const useFloodRiskPrediction = (request: {
  zone_ids?: string[];
  time_horizon?: number;
}) => {
  return useQuery({
    queryKey: ['flood-risk-prediction', request],
    queryFn: () => fetchFromApi<FloodRiskPrediction>('/predict/flood-risk', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    }),
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 15, // Refresh every 15 minutes
    enabled: !!(request.zone_ids?.length || request.time_horizon),
  });
};