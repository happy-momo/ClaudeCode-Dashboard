export type Scope = 'project' | 'global';

export type Source = 'project_native' | 'global_native' | 'project_plugin' | 'global_plugin';

export type SettingsScope = 'user' | 'project' | 'local';

export type ResourceScope = 'user' | 'project' | 'local' | 'managed' | 'plugin' | 'internal';

export interface OverrideInfo {
  overriddenBy: Scope;
  overriddenSource: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
}

export interface EffectiveCapability {
  name: string;
  type: 'skill' | 'mcp';
  scope: Scope;
  source: Source;
  active: boolean;
  overridden_by: string | null;
  plugin_name: string | null;
}

// New types for discovery API
export interface ResourceItem {
  id: string;
  name: string;
  scope: ResourceScope;
  source: string;
  path: string;
  editable: boolean;
  version?: string;
}

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
    scope: 'managed';
    source: 'managed';
    editable: false;
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

export interface ClaudeCliStatus {
  installed: boolean;
  version: string | null;
  path: string | null;
  warnings: string[];
}

export interface OperationPlan {
  operation: string;
  resource_type: string;
  target: string;
  mode: 'cli' | 'file' | 'readonly' | 'unsupported';
  reason: string;
  risk_level: 'low' | 'medium' | 'high';
  requires_restart: boolean;
  requires_reload_plugins: boolean;
  warnings: string[];
  confirmation_required: boolean;
}
