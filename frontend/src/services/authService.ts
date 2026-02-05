import axios from 'axios';
import apiClient from '../lib/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
const API_ROOT = API_URL.replace(/\/api\/?$/, '');

const authClient = axios.create({
  baseURL: API_ROOT,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export interface LoginCredentials {
  email: string;
  password: string;
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
  status: 'regular' | 'admin';
}

export const authService = {
  // Login user and get JWT tokens
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await authClient.post<LoginResponse>('/auth/token/', {
      username: credentials.email, // Backend uses username field
      password: credentials.password,
    });
    return response.data;
  },

  // Get current user profile
  async getUserProfile(): Promise<UserProfile> {
    const response = await authClient.get<UserProfile>('/auth/user/');
    return response.data;
  },

  // Refresh token
  async refreshToken(refreshToken: string): Promise<{ access: string }> {
    const response = await authClient.post('/auth/token/refresh/', {
      refresh: refreshToken,
    });
    return response.data;
  },
};
