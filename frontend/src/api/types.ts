export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiErrorBody {
  detail?: string;
  error?: string;
  details?: Record<string, unknown>;
}
