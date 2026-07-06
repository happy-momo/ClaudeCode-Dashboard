import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pluginsApi } from '@/api/plugins';
import type { InstallPluginRequest, InstallLocalPluginRequest, UpdateVersionRequest } from '@/types/plugin';

export function usePlugins() {
  return useQuery({
    queryKey: ['plugins'],
    queryFn: () => pluginsApi.list(),
  });
}

export function usePluginCatalog() {
  return useQuery({
    queryKey: ['plugin-catalog'],
    queryFn: () => pluginsApi.listCatalog(),
  });
}

export function useInstallPlugin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InstallPluginRequest) => pluginsApi.install(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['plugin-catalog'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useInstallLocalPlugin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InstallLocalPluginRequest) => pluginsApi.installLocal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['plugin-catalog'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useUpdatePluginVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateVersionRequest }) =>
      pluginsApi.updateVersion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['plugin-catalog'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useTogglePlugin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      pluginsApi.toggle(id, active),
    onSuccess: () => {
      // Invalidate and refetch to get the latest state from backend
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useUninstallPlugin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pluginsApi.uninstall(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['plugin-catalog'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}
