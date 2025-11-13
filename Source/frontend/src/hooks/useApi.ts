import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

// Generic fetch function
const apiFetch = async <T>(endpoint: string): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

// Zones API
export const useZones = () => {
  return useQuery({
    queryKey: ['zones'],
    queryFn: () => apiFetch('/api/zones'),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Risk API
export const useRisk = (timestamp?: string) => {
  const timeParam = timestamp ? `?at=${timestamp}` : '';
  return useQuery({
    queryKey: ['risk', timestamp],
    queryFn: () => apiFetch(`/api/risk${timeParam}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Damage Index API
export const useDamageIndex = () => {
  return useQuery({
    queryKey: ['damage-index'],
    queryFn: () => apiFetch('/api/damage-index'),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Resources API
export const useResources = () => {
  return useQuery({
    queryKey: ['resources'],
    queryFn: () => apiFetch('/api/resources'),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Plan API
export const usePlan = () => {
  return useQuery({
    queryKey: ['plan'],
    queryFn: () => apiFetch('/api/plan'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Alerts API
export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: () => apiFetch('/api/alerts'),
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
  });
};

// Communications API
export const useCommunications = () => {
  return useQuery({
    queryKey: ['communications'],
    queryFn: () => apiFetch('/api/comms'),
    refetchInterval: 10 * 1000, // Refresh every 10 seconds
  });
};

// Gauges API
export const useGauges = () => {
  return useQuery({
    queryKey: ['gauges'],
    queryFn: () => apiFetch('/api/gauges'),
    refetchInterval: 15 * 1000, // Refresh every 15 seconds
  });
};