import { useQuery } from '@tanstack/react-query';
import { buildApiUrl } from '@/lib/apiBase';
import type {
  PipelineAllocationsResponse,
  PipelineScenarioInfo,
  PipelineScenarioSummary,
  PipelineStatusMap,
} from '@/types';

const fetchPipelineJson = async <T>(endpoint: string): Promise<T> => {
  const response = await fetch(buildApiUrl(endpoint));

  if (!response.ok) {
    const message = await response.text();
    throw new Error(
      `Pipeline API error ${response.status}: ${message || response.statusText}`
    );
  }

  const payload = await response.json();
  return payload as T;
};

export const usePipelineScenarios = () => {
  return useQuery({
    queryKey: ['pipeline', 'scenarios'],
    queryFn: async () => {
      const payload = await fetchPipelineJson<{ scenarios: PipelineScenarioInfo[] }>(
        '/pipeline/scenarios'
      );
      return payload.scenarios;
    },
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60 * 5,
  });
};

export const useScenarioSummary = (scenario?: string | null) => {
  return useQuery({
    queryKey: ['pipeline', 'summary', scenario],
    queryFn: async () => {
      if (!scenario) {
        throw new Error('Scenario is required to fetch summary');
      }

      const payload = await fetchPipelineJson<{ summary: PipelineScenarioSummary }>(
        `/pipeline/scenarios/${scenario}/summary`
      );
      return payload.summary;
    },
    enabled: Boolean(scenario),
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60 * 5,
  });
};

export interface UseScenarioAllocationsOptions {
  scenario?: string | null;
  limit?: number;
  latest?: boolean;
  zone?: string;
  impact?: string;
  criticalOnly?: boolean;
  enabled?: boolean;
}

export const useScenarioAllocations = ({
  scenario,
  limit,
  latest,
  zone,
  impact,
  criticalOnly,
  enabled = true,
}: UseScenarioAllocationsOptions) => {
  return useQuery({
    queryKey: [
      'pipeline',
      'allocations',
      scenario,
      limit ?? null,
      latest ?? false,
      zone ?? null,
      impact ?? null,
      criticalOnly ?? false,
    ],
    queryFn: async () => {
      if (!scenario) {
        throw new Error('Scenario is required to fetch allocations');
      }

      const params = new URLSearchParams();

      if (limit) params.set('limit', String(limit));
      if (latest) params.set('latest', 'true');
      if (zone) params.set('zone', zone);
      if (impact) params.set('impact', impact);
      if (criticalOnly) params.set('criticalOnly', 'true');

      const query = params.toString() ? `?${params.toString()}` : '';
      return fetchPipelineJson<PipelineAllocationsResponse>(
        `/pipeline/scenarios/${scenario}/allocations${query}`
      );
    },
    enabled: Boolean(scenario) && enabled,
    staleTime: 1000 * 60 * 2,
    refetchInterval: 1000 * 60 * 2,
  });
};

export const usePipelineStatus = () => {
  return useQuery({
    queryKey: ['pipeline', 'status'],
    queryFn: () => fetchPipelineJson<PipelineStatusMap>('/pipeline/status'),
    staleTime: 1000 * 60 * 2,
    refetchInterval: 1000 * 60 * 2,
    retry: false,
  });
};
