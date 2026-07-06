import { apiClient } from './client';

export interface DiscoveryResult {
  user: {
    settings: {
      id: string;
      name: string;
      scope: string;
      source: string;
      path: string;
      exists: boolean;
      editable: boolean;
    };
    skills: ResourceItem[];
  };
  project: {
    settings: {
      id: string;
      name: string;
      scope: string;
      source: string;
      path: string;
      local_path: string;
      exists: boolean;
      local_exists: boolean;
      editable: boolean;
    };
    skills: ResourceItem[];
  };
  managed: {
    id: string;
    name: string;
    scope: string;
    source: string;
    editable: boolean;
    settings: Record<string, unknown>;
    mcp: Record<string, unknown>;
    extra: Record<string, unknown>[];
    warnings: string[];
  };
  plugin_cache: ResourceItem[];
  cli: {
    id: string;
    name: string;
    scope: string;
    source: string;
    installed: boolean;
    version: string | null;
    editable: boolean;
  };
  summary: {
    total_skills: number;
    total_plugin_cache: number;
    editable_count: number;
    readonly_count: number;
  };
}

export interface ResourceItem {
  id: string;
  name: string;
  scope: string;
  source: string;
  path: string;
  editable: boolean;
  version?: string;
}

export const discoveryApi = {
  /** Discover all Claude Code resources */
  getAll: (projectRoot?: string) => {
    const params = projectRoot ? `?project_root=${encodeURIComponent(projectRoot)}` : '';
    return apiClient.get<DiscoveryResult>(`/discovery/${params}`);
  },

  /** Get Claude CLI status */
  getCliStatus: () =>
    apiClient.get<DiscoveryResult['cli']>('/discovery/cli'),

  /** Get managed configuration (read-only) */
  getManaged: () =>
    apiClient.get<DiscoveryResult['managed']>('/discovery/managed'),

  /** List user-level skills */
  getUserSkills: () =>
    apiClient.get<ResourceItem[]>('/discovery/user/skills'),

  /** List project-level skills */
  getProjectSkills: (projectRoot?: string) => {
    const params = projectRoot ? `?project_root=${encodeURIComponent(projectRoot)}` : '';
    return apiClient.get<ResourceItem[]>(`/discovery/project/skills${params}`);
  },

  /** List plugin cache entries (read-only) */
  getPluginCache: () =>
    apiClient.get<ResourceItem[]>('/discovery/plugin-cache'),
};
