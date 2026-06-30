import { AxiosError } from 'axios';

/**
 * Turns an API/mutation error into a user-facing message.
 * Mirrors the previous inline behaviour: show serialized response data, else a fallback.
 */
export function parseApiError(error: unknown, fallback = 'Błąd zapisu.'): string {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as { detail?: unknown };
    if (typeof data.detail === 'string') return data.detail;
    return JSON.stringify(data.detail ?? data);
  }
  return fallback;
}
