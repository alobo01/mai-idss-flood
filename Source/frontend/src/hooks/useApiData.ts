import { useQuery } from '@tanstack/react-query';
import { buildApiUrl } from '@/lib/apiBase';
import type {
  GeoJSON,
  RiskPoint,
  Resources,
  Alert,
  Gauge,
  Communication,
  DamageIndex,
  TimeHorizon,
  FloodSimulationState,
  RiverLevelPrediction
} from '@/types';

// Generic fetch function
const fetchFromApi = async <T>(endpoint: string): Promise<T> => {
  const response = await fetch(buildApiUrl(endpoint));

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

const postToApi = async <T>(endpoint: string, body: unknown): Promise<T> => {
  const response = await fetch(buildApiUrl(endpoint), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

// Hook for fetching zones data
export const useZones = () => {
  return useQuery({
    queryKey: ['zones'],
    queryFn: () => fetchFromApi<GeoJSON>('/zones'),
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 2, // Refresh every 2 minutes
  });
};

// Hook for fetching risk data
export const useRiskData = (timestamp?: string, timeHorizon: TimeHorizon = '12h') => {
  const params = new URLSearchParams();
  if (timestamp) {
    params.append('at', timestamp);
  }
  if (timeHorizon) {
    params.append('timeHorizon', timeHorizon);
  }
  const query = params.toString();
  const riskEndpoint = query ? `/risk?${query}` : '/risk';

  return useQuery({
    queryKey: ['risk', timestamp, timeHorizon],
    queryFn: () => fetchFromApi<RiskPoint[]>(riskEndpoint),
    staleTime: 1000 * 10, // 10 seconds to keep UI snappy during simulation
    refetchInterval: 1000 * 15, // Align with simulation tick (1h every 15s)
  });
};

// Hook for fetching resources data
export const useResources = () => {
  return useQuery({
    queryKey: ['resources'],
    queryFn: () => fetchFromApi<Resources>('/resources'),
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 2, // Refresh every 2 minutes
  });
};

// Hook for fetching alerts
export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: () => fetchFromApi<Alert[]>('/alerts'),
    staleTime: 1000 * 30, // 30 seconds
    refetchInterval: 1000 * 15, // Refresh every 15 seconds for real-time feel
  });
};

// Hook for fetching gauges
export const useGauges = () => {
  return useQuery({
    queryKey: ['gauges'],
    queryFn: () => fetchFromApi<Gauge[]>('/gauges'),
    staleTime: 1000 * 60, // 1 minute
    refetchInterval: 1000 * 30, // Refresh every 30 seconds
  });
};

// Hook for fetching communications
export const useCommunications = () => {
  return useQuery({
    queryKey: ['communications'],
    queryFn: () => fetchFromApi<Communication[]>('/comms'),
    staleTime: 1000 * 60, // 1 minute
    refetchInterval: 1000 * 30, // Refresh every 30 seconds
  });
};

// Hook for fetching damage index
export const useDamageIndex = () => {
  return useQuery({
    queryKey: ['damageIndex'],
    queryFn: () => fetchFromApi<DamageIndex[]>('/damage-index'),
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 2, // Refresh every 2 minutes
  });
};

// Hook for fetching plan data
export const usePlan = () => {
  return useQuery({
    queryKey: ['plan'],
    queryFn: () => fetchFromApi<any>('/plan'),
    staleTime: 1000 * 60 * 10, // 10 minutes
    refetchInterval: 1000 * 60 * 5, // Refresh every 5 minutes
  });
};

// Hook for St. Louis-focused flood simulation
export const useFloodSimulation = (
  intervalSeconds = 10,
  intensity = 1.0,
  horizonHours = 6
) => {
  return useQuery({
    queryKey: ['flood-simulation', intervalSeconds, intensity, horizonHours],
    queryFn: () =>
      postToApi<FloodSimulationState>('/simulations/flood/step', {
        interval_seconds: intervalSeconds,
        intensity,
        horizon_hours: horizonHours,
      }),
    refetchInterval: intervalSeconds * 1000,
    refetchIntervalInBackground: true,
    staleTime: intervalSeconds * 1000 * 0.8,
  });
};

// River level predictions from backend model (no mock/simulation)
export const useRiverPredictions = () => {
  return useQuery({
    queryKey: ['river-predictions'],
    queryFn: () => fetchFromApi<RiverLevelPrediction[]>('/predict/river-level'),
    refetchInterval: 1000 * 30,
    staleTime: 1000 * 20,
  });
};

// Hook for acknowledging alerts (mutation)
export const useAcknowledgeAlert = () => {
  const acknowledgeAlert = async (alertId: string) => {
    const response = await fetch(buildApiUrl(`/alerts/${alertId}/ack`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to acknowledge alert: ${response.status}`);
    }

    return response.json();
  };

  return { acknowledgeAlert };
};

// Hook for sending communications (mutation)
export const useSendCommunication = () => {
  const sendCommunication = async (data: {
    channel: string;
    from: string;
    text: string;
  }) => {
    const response = await fetch(buildApiUrl('/comms'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to send communication: ${response.status}`);
    }

    return response.json();
  };

  return { sendCommunication };
};
