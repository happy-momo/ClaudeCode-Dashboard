import type { Scope, OverrideInfo } from './common';

export interface McpServerConfig {
  command: string;
  args?: string[];
  env?: Record<string, string>;
}

export interface McpServer {
  name: string;
  config: McpServerConfig;
  scope: Scope;
  active: boolean;
  overridden?: OverrideInfo;
  source?: string;
}

export interface McpServerResponse {
  name: string;
  config: McpServerConfig;
  scope: Scope;
  active: boolean;
  overridden?: Record<string, unknown> | null;
  source?: string;
}

export interface CreateMcpRequest {
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  scope: Scope;
}

export type ConnectivityStatus = 'unknown' | 'testing' | 'connected' | 'error';

export interface ConnectivityResult {
  name: string;
  status: ConnectivityStatus;
  message?: string;
  latency?: number;
}

export interface McpConflict {
  name: string;
  project_config: McpServerConfig;
  global_config: McpServerConfig;
}
