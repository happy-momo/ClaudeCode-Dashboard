import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { conversationsApi } from '@/api/conversations';

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationsApi.list(),
  });
}

export function useConversationDetail(sessionId: string) {
  return useQuery({
    queryKey: ['conversations', sessionId],
    queryFn: () => conversationsApi.get(sessionId),
    enabled: !!sessionId,
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => conversationsApi.delete(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}
