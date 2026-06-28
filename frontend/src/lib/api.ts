import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';
import { attachBackendWakeupInterceptors } from '@/lib/backendWakeup';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
const API_ROOT = API_URL.replace(/\/api\/?$/, '');

const refreshClient = axios.create();
attachBackendWakeupInterceptors(refreshClient);

export const clearSessionAndRedirect = () => {
  useAuthStore.getState().logout();
  if (window.location.pathname !== '/login') {
    window.location.assign('/login');
  }
};

export const refreshSession = async () => {
  const refreshToken = localStorage.getItem('refresh_token');

  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await refreshClient.post(`${API_ROOT}/auth/token/refresh`, {
    refresh: refreshToken,
  });

  const { access, refresh } = response.data;
  localStorage.setItem('access_token', access);
  if (refresh) {
    localStorage.setItem('refresh_token', refresh);
  }

  return access;
};

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
});
attachBackendWakeupInterceptors(apiClient);

// Request interceptor - Add JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const access = await refreshSession();

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        clearSessionAndRedirect();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
