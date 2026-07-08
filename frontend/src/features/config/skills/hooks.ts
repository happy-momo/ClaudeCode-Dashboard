import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { skillsApi, type ImportSkillRequest } from '@/api/skills';

export function useSkills(scope: string = 'project') {
  return useQuery({
    queryKey: ['skills', scope],
    queryFn: () => skillsApi.list(scope),
  });
}

export function useCreateSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; content: string; scope: string }) => skillsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useUpdateSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, data }: { name: string; data: { content: string; scope?: string } }) =>
      skillsApi.update(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useImportSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ImportSkillRequest) => skillsApi.import(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}

export function useDeleteSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, scope }: { name: string; scope: string }) =>
      skillsApi.delete(name, scope),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      queryClient.invalidateQueries({ queryKey: ['effective-capabilities'] });
    },
  });
}
