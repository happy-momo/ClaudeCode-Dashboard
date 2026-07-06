import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { systemApi } from '@/api/system';
import { skillsApi } from '@/api/skills';
import { mcpApi } from '@/api/mcp';

export function useEffectiveCapabilities() {
  return useQuery({
    queryKey: ['effective-capabilities'],
    queryFn: () => systemApi.getEffectiveCapabilities(),
  });
}

export function useDeleteCapability() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, type, scope }: { name: string; type: 'skill' | 'mcp'; scope: string }) => {
      if (type === 'skill') {
        return skillsApi.delete(name, scope);
      } else {
        return mcpApi.remove(name, scope);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });
}
