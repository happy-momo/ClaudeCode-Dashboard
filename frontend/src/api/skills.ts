import { apiClient } from './client';

export interface SkillResponse {
  name: string;
  description: string;
  content: string;
  scope: 'project' | 'global';
  active: boolean;
  overridden?: Record<string, unknown>;
  source?: string;
  path?: string;
}

export interface ImportSkillRequest {
  name: string;
  content: string;
  scope: 'project' | 'global';
  format: string;
}

export const skillsApi = {
  list: (scope: string = 'project') =>
    apiClient.get<SkillResponse[]>(`/skills?scope=${scope}`),

  get: (name: string, scope: string = 'project') =>
    apiClient.get<SkillResponse>(`/skills/${encodeURIComponent(name)}?scope=${scope}`),

  create: (data: { name: string; content: string; scope: string }) =>
    apiClient.post<SkillResponse>('/skills', data),

  import: (data: ImportSkillRequest) =>
    apiClient.post<SkillResponse>('/skills/import', data),

  update: (name: string, data: { content: string; scope?: string }) =>
    apiClient.put<SkillResponse>(`/skills/${encodeURIComponent(name)}`, data),

  delete: (name: string, scope: string = 'project') =>
    apiClient.delete(`/skills/${encodeURIComponent(name)}?scope=${scope}`),

  move: (name: string, targetScope: string, scope: string = 'project') =>
    apiClient.post(`/skills/${encodeURIComponent(name)}/move?scope=${scope}`, { target_scope: targetScope }),

  // New: fork a plugin skill to user/project scope
  fork: (name: string, fromScope: string, toScope: string) =>
    apiClient.post<SkillResponse>(`/skills/${encodeURIComponent(name)}/fork`, {
      from_scope: fromScope,
      to_scope: toScope,
    }),
};
