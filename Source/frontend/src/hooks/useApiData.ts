import { useQuery } from '@tanstack/react-query';
import { buildApiUrl } from '@/lib/apiBase';
import type {
  GeoJSON,
  RiskPoint,
  Resources,
  Alert,
  Gauge,
  Communication,
  DamageIndex
} from '@/types';

// Generic fetch function
const fetchFromApi = async <T>(endpoint: string): Promise<T> => {
  const response = await fetch(buildApiUrl(endpoint));

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
export const useRiskData = (timestamp?: string) => {
  const riskEndpoint = timestamp
    ? `/risk?at=${encodeURIComponent(timestamp)}`
    : '/risk?at=2025-11-11T12-00-00Z';

  return useQuery({
    queryKey: ['risk', timestamp],
    queryFn: () => fetchFromApi<RiskPoint[]>(riskEndpoint),
    staleTime: 1000 * 30, // 30 seconds
    refetchInterval: 1000 * 60, // Refresh every minute
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
