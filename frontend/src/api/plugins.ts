import { apiClient } from './client';
import type { PluginResponse, CatalogPluginEntry, InstallPluginRequest, InstallLocalPluginRequest, UpdateVersionRequest } from '@/types/plugin';

export interface PluginInstallResult {
  message: string;
  success: boolean;
  cli_output?: string;
}

export const pluginsApi = {
  list: () =>
    apiClient.get<PluginResponse[]>('/plugins'),

  get: (id: string) =>
    apiClient.get<PluginResponse>(`/plugins/${encodeURIComponent(id)}`),

  listCatalog: () =>
    apiClient.get<CatalogPluginEntry[]>('/plugins/catalog'),

  install: (data: InstallPluginRequest) =>
    apiClient.post<PluginInstallResult>('/plugins/install', data),

  installLocal: (data: InstallLocalPluginRequest) =>
    apiClient.post<PluginResponse>('/plugins/install-local', data),

  toggle: (id: string, active: boolean) =>
    apiClient.patch<PluginInstallResult>(`/plugins/${encodeURIComponent(id)}/toggle`, { active }),

  updateVersion: (id: string, data: UpdateVersionRequest) =>
    apiClient.patch<PluginResponse>(`/plugins/${encodeURIComponent(id)}/version`, data),

  uninstall: (id: string) =>
    apiClient.delete<PluginInstallResult>(`/plugins/${encodeURIComponent(id)}`),

  // New endpoints for CLI-first backend
  getCache: () =>
    apiClient.get<Record<string, unknown>[]>('/plugins/cache'),

  listMarketplaces: () =>
    apiClient.get<{ marketplaces: string[]; error?: string }>('/plugins/marketplaces'),

  addMarketplace: (source: string) =>
    apiClient.post<{ message: string; success: boolean }>('/plugins/marketplaces', { source }),

  updateMarketplace: (name?: string) =>
    apiClient.post<{ message: string; success: boolean }>('/plugins/marketplaces/update', { name }),
};
