import { apiClient } from './client';
import type { ContextWindow, UsageTimeSeriesPoint } from '@/types/stats';

export const statsApi = {
  getContextWindow: (sessionId: string = 'default') =>
    apiClient.get<ContextWindow>(`/stats/context?session_id=${sessionId}`),

  getUsageTimeSeries: (days: number = 7) =>
    apiClient.get<UsageTimeSeriesPoint[]>(`/stats/usage?days=${days}`),
};