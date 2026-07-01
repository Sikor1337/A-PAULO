import axios from 'axios';
import { clearSessionAndRedirect, refreshSession } from '@/lib/api';
import { attachBackendWakeupInterceptors } from '@/lib/backendWakeup';
import { isSessionChangedError } from '@/lib/sessionLifecycle';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
const API_ROOT = API_URL.replace(/\/api\/?$/, '');

const authClient = axios.create({
  baseURL: API_ROOT,
  headers: {
    'Content-Type': 'application/json',
  },
});
attachBackendWakeupInterceptors(authClient);

// Attach access token for auth endpoints that require it
authClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

authClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const url = String(error.config?.url ?? '');
    const isLoginRequest = url.includes('/auth/token') && !url.includes('/auth/token/refresh');
    const isRegisterRequest = url.includes('/auth/register');
    const isRefreshRequest = url.includes('/auth/token/refresh');
    const originalRequest = error.config;

    if (error.response?.status === 401 && !isLoginRequest && !isRegisterRequest && !isRefreshRequest && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const access = await refreshSession();
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return authClient(originalRequest);
      } catch (refreshError) {
        if (isSessionChangedError(refreshError)) {
          return Promise.reject(refreshError);
        }
        clearSessionAndRedirect();
        return Promise.reject(refreshError);
      }
    }

    if (error.response?.status === 401 && !isLoginRequest && !isRegisterRequest) {
      clearSessionAndRedirect();
    }

    return Promise.reject(error);
  },
);

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  recruitment_token?: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface UserProfile {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  status: 'new_volunteer' | 'regular' | 'admin';
  is_active?: boolean;
}

export interface UpdateProfilePayload {
  email?: string;
  first_name?: string;
  last_name?: string;
  current_password?: string;
  new_password?: string;
}

export const authService = {
  // Register new user
  async register(credentials: RegisterCredentials): Promise<UserProfile> {
    const response = await authClient.post<UserProfile>('/auth/register', {
      username: credentials.username,
      email: credentials.email,
      password: credentials.password,
      first_name: credentials.first_name || '',
      last_name: credentials.last_name || '',
      ...(credentials.recruitment_token
        ? { recruitment_token: credentials.recruitment_token }
        : {}),
    });
    return response.data;
  },

  // Login user and get JWT tokens
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await authClient.post<LoginResponse>('/auth/token', {
      username: credentials.email, // Backend uses username field
      password: credentials.password,
    });
    return response.data;
  },

  // Get current user profile
  async getUserProfile(): Promise<UserProfile> {
    const response = await authClient.get<UserProfile>('/auth/user');
    return response.data;
  },

  // Update own profile (email/name), optionally changing the password
  async updateProfile(data: UpdateProfilePayload): Promise<UserProfile> {
    const response = await authClient.patch<UserProfile>('/auth/user', data);
    return response.data;
  },

  // Refresh token
  async refreshToken(refreshToken: string): Promise<{ access: string }> {
    const response = await authClient.post('/auth/token/refresh', {
      refresh: refreshToken,
    });
    return response.data;
  },
};
