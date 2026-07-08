import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpApi } from '@/api/mcp';
import type { CreateMcpRequest, UpdateMcpRequest } from '@/types/mcp';

export function useMcpServers(scope: string = 'project') {
  return useQuery({
    queryKey: ['mcp-servers', scope],
    queryFn: () => mcpApi.list(scope),
  });
}

export function useCreateMcpServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateMcpRequest) => mcpApi.add(data),
    onSuccess: (variables) => {
      // Invalidate both project and global queries
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useUpdateMcpServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, data }: { name: string; data: UpdateMcpRequest }) =>
      mcpApi.update(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useDeleteMcpServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, scope }: { name: string; scope: string }) =>
      mcpApi.remove(name, scope),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useTestConnectivity() {
  return useMutation({
    mutationFn: ({ name, scope }: { name: string; scope: string }) =>
      mcpApi.testConnectivity(name, scope),
    onSuccess: (result) => {
      if (result.status === 'connected') {
        alert(`✅ MCP server "${result.name}" connected successfully!\nLatency: ${result.latency}ms`);
      } else {
        alert(`❌ MCP server "${result.name}" test failed:\n${result.message || 'Unknown error'}`);
      }
    },
    onError: (error) => {
      alert(`Failed to test MCP server: ${error.message}`);
    },
  });
}

export function useMcpConflicts() {
  return useQuery({
    queryKey: ['mcp-conflicts'],
    queryFn: () => mcpApi.detectConflicts(),
  });
}
