import { describe, expect, it } from 'vitest';
import apiClient from './api';

describe('apiClient', () => {
  it('does not force JSON content type for multipart requests', () => {
    expect(apiClient.defaults.headers.common['Content-Type']).toBeUndefined();
  });
});
