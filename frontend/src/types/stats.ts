export interface ContextSegment {
  label: string;
  value: number;
  color: string;
  percentage: number;
}

export interface ContextWindow {
  total: number;
  used: number;
  remaining: number;
  max_context?: number;
  maxContext?: number;
  segments: ContextSegment[];
  // Support both snake_case (from backend) and camelCase
  input_tokens?: number;
  output_tokens?: number;
  tool_calls?: number;
  inputTokens?: number;
  outputTokens?: number;
  toolCalls?: number;
  session_id?: string;
  sessionId?: string;
}

export interface UsageTimeSeriesPoint {
  date: string;
  input: number;
  output: number;
  tools: number;
  total: number;
}