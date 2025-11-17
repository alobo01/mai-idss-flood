import { useQuery } from '@tanstack/react-query';
import { buildApiUrl } from '@/lib/apiBase';

// Generic fetch function
const apiFetch = async <T>(endpoint: string): Promise<T> => {
  const response = await fetch(buildApiUrl(endpoint));

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

// Zones API
export const useZones = () => {
  return useQuery({
    queryKey: ['zones'],
    queryFn: () => apiFetch('/zones'),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Risk API
export const useRisk = (timestamp?: string) => {
  const timeParam = timestamp ? `?at=${timestamp}` : '';
  return useQuery({
    queryKey: ['risk', timestamp],
    queryFn: () => apiFetch(`/risk${timeParam}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Damage Index API
export const useDamageIndex = () => {
  return useQuery({
    queryKey: ['damage-index'],
    queryFn: () => apiFetch('/damage-index'),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Resources API
export const useResources = () => {
  return useQuery({
    queryKey: ['resources'],
    queryFn: () => apiFetch('/resources'),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Plan API
export const usePlan = () => {
  return useQuery({
    queryKey: ['plan'],
    queryFn: () => apiFetch('/plan'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Alerts API
export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: () => apiFetch('/alerts'),
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
  });
};

// Communications API
export const useCommunications = () => {
  return useQuery({
    queryKey: ['communications'],
    queryFn: () => apiFetch('/comms'),
    refetchInterval: 10 * 1000, // Refresh every 10 seconds
  });
};

// Gauges API
export const useGauges = () => {
  return useQuery({
    queryKey: ['gauges'],
    queryFn: () => apiFetch('/gauges'),
    refetchInterval: 15 * 1000, // Refresh every 15 seconds
  });
};
