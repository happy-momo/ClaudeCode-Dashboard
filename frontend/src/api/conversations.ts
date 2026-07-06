import { apiClient } from './client';
import type { ConversationResponse, ConversationDetail } from '@/types/conversation';

export const conversationsApi = {
  list: () =>
    apiClient.get<ConversationResponse[]>('/conversations'),

  get: (sessionId: string) =>
    apiClient.get<ConversationDetail>(`/conversations/${encodeURIComponent(sessionId)}`),

  delete: (sessionId: string) =>
    apiClient.delete(`/conversations/${encodeURIComponent(sessionId)}`),
};