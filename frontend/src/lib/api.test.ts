import type {
  AxiosAdapter,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { afterEach, describe, expect, it } from 'vitest';
import { queryClient } from './queryClient';
import { useAuthStore } from '@/stores/authStore';
import { SessionChangedError } from './sessionLifecycle';
import apiClient, {
  clearSessionAndRedirect,
  refreshClient,
  refreshSession,
} from './api';

const defaultRefreshAdapter = refreshClient.defaults.adapter;

afterEach(() => {
  refreshClient.defaults.adapter = defaultRefreshAdapter;
  queryClient.clear();
});

describe('apiClient', () => {
  it('does not force JSON content type for multipart requests', () => {
    expect(apiClient.defaults.headers.common['Content-Type']).toBeUndefined();
  });

  it('clears server cache during automatic logout', () => {
    window.history.replaceState({}, '', '/login');
    useAuthStore.getState().login('access-token', 'refresh-token', {
      id: 1,
      email: 'anna@example.org',
      first_name: 'Anna',
      last_name: 'Nowak',
      status: 'admin',
    });
    queryClient.setQueryData(['groups'], [{ id: 1, name: 'Grupa A' }]);

    clearSessionAndRedirect();

    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    window.history.replaceState({}, '', '/');
  });

  it('does not restore tokens when logout happens during refresh', async () => {
    let resolveResponse: ((response: AxiosResponse) => void) | undefined;
    let requestConfig: InternalAxiosRequestConfig | undefined;
    const adapter: AxiosAdapter = (config) =>
      new Promise((resolve) => {
        requestConfig = config;
        resolveResponse = resolve;
        expect(config.url).toContain('/auth/token/refresh');
      });
    refreshClient.defaults.adapter = adapter;
    useAuthStore.getState().login('old-access', 'old-refresh', {
      id: 1,
      email: 'anna@example.org',
      first_name: 'Anna',
      last_name: 'Nowak',
      status: 'admin',
    });

    const refreshPromise = refreshSession();
    await Promise.resolve();
    await Promise.resolve();
    expect(resolveResponse).toBeDefined();
    useAuthStore.getState().logout();
    resolveResponse?.({
      config: requestConfig!,
      data: { access: 'new-access', refresh: 'new-refresh' },
      headers: {},
      status: 200,
      statusText: 'OK',
    });

    await expect(refreshPromise).rejects.toBeInstanceOf(SessionChangedError);
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
