import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpApi } from '@/api/mcp';
import type { CreateMcpRequest } from '@/types/mcp';

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
  });
}

export function useMcpConflicts() {
  return useQuery({
    queryKey: ['mcp-conflicts'],
    queryFn: () => mcpApi.detectConflicts(),
  });
}
