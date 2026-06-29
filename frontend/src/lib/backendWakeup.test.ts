import axios from 'axios';
import type {
  AxiosAdapter,
  AxiosProgressEvent,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  attachBackendWakeupInterceptors,
  BACKEND_WAKEUP_DELAY_MS,
  getBackendWakeupSnapshot,
  resetBackendWakeupNotice,
} from './backendWakeup';

const flushInterceptors = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

const progressEvent = (
  loaded: number,
  total: number,
): AxiosProgressEvent => ({
  loaded,
  total,
  progress: loaded / total,
  bytes: loaded,
  lengthComputable: true,
});

describe('backend wakeup Axios interceptors', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    resetBackendWakeupNotice();
  });

  afterEach(() => {
    resetBackendWakeupNotice();
    vi.useRealTimers();
  });

  it('hides the notice when the first response byte arrives', async () => {
    let requestConfig: InternalAxiosRequestConfig | undefined;
    let resolveResponse: ((response: AxiosResponse) => void) | undefined;
    const adapter: AxiosAdapter = (config) =>
      new Promise((resolve) => {
        requestConfig = config;
        resolveResponse = resolve;
      });
    const client = axios.create({ adapter });
    attachBackendWakeupInterceptors(client);

    const request = client.get('/slow');
    await flushInterceptors();
    expect(requestConfig).toBeDefined();

    vi.advanceTimersByTime(BACKEND_WAKEUP_DELAY_MS);
    expect(getBackendWakeupSnapshot()).toBe(true);

    requestConfig?.onDownloadProgress?.(progressEvent(1, 100));
    expect(getBackendWakeupSnapshot()).toBe(false);

    resolveResponse?.({
      config: requestConfig!,
      data: {},
      headers: {},
      status: 200,
      statusText: 'OK',
    });
    await request;
  });

  it('starts the response timer after a multipart upload completes', async () => {
    let requestConfig: InternalAxiosRequestConfig | undefined;
    let resolveResponse: ((response: AxiosResponse) => void) | undefined;
    const adapter: AxiosAdapter = (config) =>
      new Promise((resolve) => {
        requestConfig = config;
        resolveResponse = resolve;
      });
    const client = axios.create({ adapter });
    attachBackendWakeupInterceptors(client);
    const form = new FormData();
    form.append('content', new Blob(['file']), 'card.pdf');

    const request = client.post('/upload', form);
    await flushInterceptors();
    expect(requestConfig).toBeDefined();

    vi.advanceTimersByTime(BACKEND_WAKEUP_DELAY_MS);
    expect(getBackendWakeupSnapshot()).toBe(false);

    requestConfig?.onUploadProgress?.(progressEvent(100, 100));
    vi.advanceTimersByTime(BACKEND_WAKEUP_DELAY_MS);
    expect(getBackendWakeupSnapshot()).toBe(true);

    requestConfig?.onDownloadProgress?.(progressEvent(1, 100));
    expect(getBackendWakeupSnapshot()).toBe(false);

    resolveResponse?.({
      config: requestConfig!,
      data: {},
      headers: {},
      status: 200,
      statusText: 'OK',
    });
    await request;
  });

  it('does not restart tracking after logout resets active requests', async () => {
    let requestConfig: InternalAxiosRequestConfig | undefined;
    let resolveResponse: ((response: AxiosResponse) => void) | undefined;
    const adapter: AxiosAdapter = (config) =>
      new Promise((resolve) => {
        requestConfig = config;
        resolveResponse = resolve;
      });
    const client = axios.create({ adapter });
    attachBackendWakeupInterceptors(client);
    const form = new FormData();
    form.append('content', new Blob(['file']), 'card.pdf');

    const request = client.post('/upload', form);
    await flushInterceptors();
    resetBackendWakeupNotice();
    requestConfig?.onUploadProgress?.(progressEvent(100, 100));
    vi.advanceTimersByTime(BACKEND_WAKEUP_DELAY_MS);

    expect(getBackendWakeupSnapshot()).toBe(false);
    resolveResponse?.({
      config: requestConfig!,
      data: {},
      headers: {},
      status: 200,
      statusText: 'OK',
    });
    await request;
  });
});
