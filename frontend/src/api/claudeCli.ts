import { apiClient } from './client';

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

export const claudeCliApi = {
  /** Get Claude CLI installation status */
  getStatus: () =>
    apiClient.get<ClaudeCliStatus>('/claude/status'),

  /** Debug: test operation planning */
  runPlan: (operation: string, resourceType: string, target: string, scope: string = 'project') =>
    apiClient.post<OperationPlan>('/claude/run-plan', {
      operation,
      resource_type: resourceType,
      target,
      scope,
    }),
};
