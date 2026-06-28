import { describe, expect, it } from 'vitest';
import { queryClient } from './queryClient';
import { useAuthStore } from '@/stores/authStore';
import apiClient, { clearSessionAndRedirect } from './api';

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
      role: 'admin',
    });
    queryClient.setQueryData(['groups'], [{ id: 1, name: 'Grupa A' }]);

    clearSessionAndRedirect();

    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    window.history.replaceState({}, '', '/');
  });
});
