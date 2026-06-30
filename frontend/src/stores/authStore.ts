import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserStatus } from '@/types';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  status: UserStatus;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

interface LegacyPersistedUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  status?: UserStatus;
  role?: string;
}

export const migrateAuthState = (persistedState: unknown): unknown => {
  const state = persistedState as { user?: LegacyPersistedUser | null };
  const user = state?.user;
  if (!user || user.status) return persistedState;

  return {
    ...state,
    user: {
      id: user.id,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      status: user.role === 'admin' ? 'admin' : 'regular',
    },
  };
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: !!localStorage.getItem('access_token'),

      login: (accessToken: string, refreshToken: string, user: User) => {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        set({ user, isAuthenticated: true });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, isAuthenticated: false });
      },

      updateUser: (user: User) => {
        set({ user });
      },
    }),
    {
      name: 'auth-user',
      version: 1,
      migrate: (persistedState) => migrateAuthState(persistedState) as AuthState,
      // Persist only the user profile; auth status is derived from the token in localStorage.
      partialize: (state) => ({ user: state.user }),
    },
  ),
);
