import { apiClient } from './client';

export interface ManagedSettings {
  settings: Record<string, unknown>;
  mcp: Record<string, unknown>;
  extra: Record<string, unknown>[];
  editable: false;
  source: 'managed';
  warnings?: string[];
}

export const managedApi = {
  /** Get all managed configuration (read-only) */
  getAll: () =>
    apiClient.get<ManagedSettings>('/managed/'),

  /** Get managed settings only */
  getSettings: () =>
    apiClient.get<{ settings: Record<string, unknown>; warning?: string }>('/managed/settings'),

  /** Get managed MCP servers only */
  getMcp: () =>
    apiClient.get<{ mcp: Record<string, unknown>; warning?: string }>('/managed/mcp'),
};
