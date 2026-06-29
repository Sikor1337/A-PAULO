import type {
  AxiosInstance,
  AxiosProgressEvent,
  InternalAxiosRequestConfig,
} from 'axios';

export const BACKEND_WAKEUP_DELAY_MS = 5_000;

type RequestCleanup = () => void;
type Listener = () => void;

const listeners = new Set<Listener>();
const pendingTimers = new Map<symbol, ReturnType<typeof setTimeout>>();
const slowRequests = new Set<symbol>();
let isBackendWakeupVisible = false;
let trackingRevision = 0;

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
  trackingRevision += 1;
  pendingTimers.forEach((timer) => clearTimeout(timer));
  pendingTimers.clear();
  slowRequests.clear();
  notifyIfChanged();
};

export const attachBackendWakeupInterceptors = (client: AxiosInstance) => {
  const cleanups = new WeakMap<InternalAxiosRequestConfig, RequestCleanup>();
  const settledRequests = new WeakSet<InternalAxiosRequestConfig>();

  const finishRequest = (
    config?: InternalAxiosRequestConfig,
    settled = false,
  ) => {
    if (!config) return;
    if (settled) settledRequests.add(config);
    cleanups.get(config)?.();
    cleanups.delete(config);
  };

  client.interceptors.request.use((config) => {
    const requestRevision = trackingRevision;
    const originalDownloadProgress = config.onDownloadProgress;
    const originalUploadProgress = config.onUploadProgress;
    const isMultipartUpload =
      typeof FormData !== 'undefined' && config.data instanceof FormData;

    const startTracking = () => {
      if (
        settledRequests.has(config) ||
        requestRevision !== trackingRevision
      ) {
        return;
      }
      finishRequest(config);
      cleanups.set(config, startBackendRequest());
    };

    if (isMultipartUpload) {
      config.onUploadProgress = (event: AxiosProgressEvent) => {
        const uploadComplete =
          (event.total !== undefined && event.loaded >= event.total) ||
          event.progress === 1;
        if (uploadComplete) startTracking();
        originalUploadProgress?.(event);
      };
    } else {
      startTracking();
    }

    config.onDownloadProgress = (event: AxiosProgressEvent) => {
      finishRequest(config, true);
      originalDownloadProgress?.(event);
    };

    return config;
  });

  client.interceptors.response.use(
    (response) => {
      finishRequest(response.config, true);
      return response;
    },
    (error) => {
      finishRequest(error.config, true);
      return Promise.reject(error);
    },
  );
};
