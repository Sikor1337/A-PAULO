import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

export const BACKEND_WAKEUP_DELAY_MS = 5_000;

type RequestCleanup = () => void;
type Listener = () => void;

const listeners = new Set<Listener>();
const pendingTimers = new Map<symbol, ReturnType<typeof setTimeout>>();
const slowRequests = new Set<symbol>();
let isBackendWakeupVisible = false;

const notifyIfChanged = () => {
  const nextValue = slowRequests.size > 0;
  if (nextValue === isBackendWakeupVisible) return;

  isBackendWakeupVisible = nextValue;
  listeners.forEach((listener) => listener());
};

export const subscribeToBackendWakeup = (listener: Listener) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

export const getBackendWakeupSnapshot = () => isBackendWakeupVisible;

export const startBackendRequest = (): RequestCleanup => {
  const requestId = Symbol('backend-request');
  const timer = setTimeout(() => {
    pendingTimers.delete(requestId);
    slowRequests.add(requestId);
    notifyIfChanged();
  }, BACKEND_WAKEUP_DELAY_MS);

  pendingTimers.set(requestId, timer);

  return () => {
    const pendingTimer = pendingTimers.get(requestId);
    if (pendingTimer) {
      clearTimeout(pendingTimer);
      pendingTimers.delete(requestId);
    }

    if (slowRequests.delete(requestId)) {
      notifyIfChanged();
    }
  };
};

export const resetBackendWakeupNotice = () => {
  pendingTimers.forEach((timer) => clearTimeout(timer));
  pendingTimers.clear();
  slowRequests.clear();
  notifyIfChanged();
};

export const attachBackendWakeupInterceptors = (client: AxiosInstance) => {
  const cleanups = new WeakMap<InternalAxiosRequestConfig, RequestCleanup>();

  const finishRequest = (config?: InternalAxiosRequestConfig) => {
    if (!config) return;
    cleanups.get(config)?.();
    cleanups.delete(config);
  };

  client.interceptors.request.use((config) => {
    cleanups.set(config, startBackendRequest());
    return config;
  });

  client.interceptors.response.use(
    (response) => {
      finishRequest(response.config);
      return response;
    },
    (error) => {
      finishRequest(error.config);
      return Promise.reject(error);
    },
  );
};
