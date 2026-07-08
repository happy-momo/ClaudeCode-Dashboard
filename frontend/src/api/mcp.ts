import { apiClient } from './client';
import type { McpServerResponse, CreateMcpRequest, UpdateMcpRequest, ConnectivityResult, McpConflict } from '@/types/mcp';

export const mcpApi = {
  list: (scope: string = 'project') =>
    apiClient.get<McpServerResponse[]>(`/mcp?scope=${scope}`),

  add: (data: CreateMcpRequest) =>
    apiClient.post<McpServerResponse>('/mcp', data),

  update: (name: string, data: UpdateMcpRequest) =>
    apiClient.put<McpServerResponse>(`/mcp/${encodeURIComponent(name)}`, data),

  remove: (name: string, scope: string = 'project') =>
    apiClient.delete(`/mcp/${encodeURIComponent(name)}?scope=${scope}`),

  testConnectivity: (name: string, scope: string = 'project') =>
    apiClient.post<ConnectivityResult>(`/mcp/${encodeURIComponent(name)}/test?scope=${scope}`),

  detectConflicts: () =>
    apiClient.get<McpConflict[]>('/mcp/conflicts'),
};
