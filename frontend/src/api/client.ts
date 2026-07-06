/// <reference types="vite/client" />

export class ApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(status: number, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

/**
 * Get current session ID from URL parameters.
 */
function getCurrentSessionId(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get('session_id');
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const sessionId = getCurrentSessionId();

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      // Automatically attach session ID header if available
      ...(sessionId && { 'X-Claude-Session-Id': sessionId }),
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorData: Record<string, unknown> = {};
    try {
      errorData = await response.json();
    } catch {
      // ignore parse error
    }
    throw new ApiError(
      response.status,
      (errorData.detail as string) || (errorData.error as string) || response.statusText,
      errorData
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const apiClient = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(endpoint: string, body: unknown) =>
    request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  patch: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),
};
