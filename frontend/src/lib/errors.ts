import { AxiosError } from 'axios';

/**
 * Turns an API/mutation error into a user-facing message.
 * Mirrors the previous inline behaviour: show serialized response data, else a fallback.
 */
export function parseApiError(error: unknown, fallback = 'Błąd zapisu.'): string {
  if (error instanceof AxiosError && error.response?.data) {
    return JSON.stringify(error.response.data);
  }
  return fallback;
}
