import { apiClient } from './client';
import type { EffectiveCapability } from '@/types/common';

export const systemApi = {
  getEffectiveCapabilities: () =>
    apiClient.get<EffectiveCapability[]>('/system/effective-capabilities'),
};
