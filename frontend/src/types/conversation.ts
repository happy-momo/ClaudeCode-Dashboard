export interface Conversation {
  id: string;
  title: string;
  date: string;
  tokens: number;
  turns: number;
  project?: string;
}

export interface ConversationResponse {
  id: string;
  title: string;
  date: string;
  tokens: number;
  turns: number;
  project?: string;
  project_folder?: string;
}

export interface ConversationTurn {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp?: string;
  tokens?: number;
}

export interface ConversationDetail {
  id: string;
  title: string;
  date: string;
  tokens: number;
  turns: number;
  messages: ConversationTurn[];
}