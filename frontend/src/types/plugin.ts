export type PluginLevel = 'project' | 'global';

export interface PluginResponse {
  id: string;
  name: string;
  version: string;
  description: string;
  level: string;
  scope: string;  // user, project, or local (current scope)
  active: boolean;
  skills: string[];
  mcps: string[];
  path?: string;
}

export interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  level: PluginLevel;
  active: boolean;
  skills: string[];
  mcps: string[];
  path?: string;
}

export interface CatalogPluginEntry {
  name: string;
  description: string;
  marketplace: string;
  skills_count: number;
  mcps_count: number;
  has_mcp_server: boolean;
  installed: boolean;
  installedInProject?: boolean;  // Plugin installed in project scope
  installedInGlobal?: boolean;   // Plugin installed in global scope
}

export interface InstallPluginRequest {
  plugin_name: string;
  marketplace: string;
  scope: 'project' | 'global';
}

export interface InstallLocalPluginRequest {
  path: string;
  scope: 'project' | 'global';
}

export interface UpdateVersionRequest {
  version: string;
}
