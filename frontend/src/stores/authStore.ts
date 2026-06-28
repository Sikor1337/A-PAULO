import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { resetBackendWakeupNotice } from '@/lib/backendWakeup';
import { queryClient } from '@/lib/queryClient';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'coordinator' | 'guide' | 'volunteer';
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

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
        queryClient.clear();
        resetBackendWakeupNotice();
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
      // Persist only the user profile; auth status is derived from the token in localStorage.
      partialize: (state) => ({ user: state.user }),
    },
  ),
);
