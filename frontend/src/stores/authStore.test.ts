import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { queryClient } from '@/lib/queryClient';
import { migrateAuthState, useAuthStore } from './authStore';

const user = {
  id: 1,
  email: 'anna@example.org',
  first_name: 'Anna',
  last_name: 'Nowak',
  status: 'admin' as const,
};

const resetAuthStore = () => {
  queryClient.clear();
  useAuthStore.setState({ user: null, isAuthenticated: false });
};

describe('auth store', () => {
  beforeEach(resetAuthStore);
  afterEach(resetAuthStore);

  it('stores tokens and user profile on login', () => {
    useAuthStore.getState().login('access-token', 'refresh-token', user);

    expect(localStorage.getItem('access_token')).toBe('access-token');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-token');
    expect(useAuthStore.getState()).toMatchObject({
      user,
      isAuthenticated: true,
    });
  });

  it('clears tokens and user profile on logout', () => {
    useAuthStore.getState().login('access-token', 'refresh-token', user);

    useAuthStore.getState().logout();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(useAuthStore.getState()).toMatchObject({
      user: null,
      isAuthenticated: false,
    });
  });

  it('clears all server cache on logout', () => {
    useAuthStore.getState().login('access-token', 'refresh-token', user);
    queryClient.setQueryData(['beneficiaries'], [{ id: 7, name: 'Jan' }]);
    queryClient.setQueryData(['volunteers'], [{ id: 9, name: 'Anna' }]);

    useAuthStore.getState().logout();

    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
  });

  it('updates only the current user profile', () => {
    useAuthStore.getState().login('access-token', 'refresh-token', user);

    useAuthStore.getState().updateUser({ ...user, first_name: 'Maria' });

    expect(useAuthStore.getState()).toMatchObject({
      user: { ...user, first_name: 'Maria' },
      isAuthenticated: true,
    });
    expect(localStorage.getItem('access_token')).toBe('access-token');
  });

  it('migrates the legacy role field to status', () => {
    const migrated = migrateAuthState({
      user: {
        id: 7,
        email: 'admin@example.org',
        first_name: 'Ada',
        last_name: 'Admin',
        role: 'admin',
      },
    });

    expect(migrated).toEqual({
      user: {
        id: 7,
        email: 'admin@example.org',
        first_name: 'Ada',
        last_name: 'Admin',
        status: 'admin',
      },
    });
  });
});
