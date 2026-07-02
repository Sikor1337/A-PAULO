import { AxiosError } from 'axios';

/**
 * Turns an API/mutation error into a user-facing message.
 * Mirrors the previous inline behaviour: show serialized response data, else a fallback.
 */
export function parseApiError(error: unknown, fallback = 'Błąd zapisu.'): string {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as { detail?: unknown };
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      const messages = data.detail
        .map((item) => {
          if (!item || typeof item !== 'object') return null;
          const detail = item as { msg?: unknown };
          return typeof detail.msg === 'string' ? detail.msg : null;
        })
        .filter((message): message is string => Boolean(message));
      if (messages.length) return messages.join(' ');
    }
    return JSON.stringify(data.detail ?? data);
  }
  return fallback;
}
