import { apiClient } from './client';

export interface SettingsResponse {
  [key: string]: unknown;
}

export interface PatchSettingsRequest {
  [key: string]: unknown;
}

export type SettingsScope = 'user' | 'project' | 'local';

export const settingsApi = {
  /** Get settings for a specific scope */
  get: (scope: SettingsScope) =>
    apiClient.get<SettingsResponse>(`/settings/${scope}`),

  /** Patch settings for a specific scope */
  patch: (scope: SettingsScope, update: PatchSettingsRequest) =>
    apiClient.patch<SettingsResponse>(`/settings/${scope}`, update),
};
