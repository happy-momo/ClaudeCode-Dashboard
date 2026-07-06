import { useQuery } from '@tanstack/react-query';
import { statsApi } from '@/api/stats';

export function useContextWindow(sessionId: string = 'default') {
  return useQuery({
    queryKey: ['stats', 'context-window', sessionId],
    queryFn: () => statsApi.getContextWindow(sessionId),
    refetchInterval: 10_000,
  });
}

export function useUsageTimeSeries(days: number = 14) {
  return useQuery({
    queryKey: ['stats', 'usage-time-series', days],
    queryFn: () => statsApi.getUsageTimeSeries(days),
  });
}