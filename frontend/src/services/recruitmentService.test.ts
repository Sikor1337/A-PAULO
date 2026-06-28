import { beforeEach, describe, expect, it, vi } from 'vitest';
import apiClient from '@/lib/api';
import { recruitmentService } from './recruitmentService';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedApiClient = vi.mocked(apiClient);

describe('recruitmentService', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('loads every submissions page instead of stopping at the backend default', async () => {
    const firstPage = Array.from({ length: 1000 }, (_, id) => ({ id }));
    const secondPage = [{ id: 1000 }];
    mockedApiClient.get
      .mockResolvedValueOnce({ data: firstPage })
      .mockResolvedValueOnce({ data: secondPage });

    const result = await recruitmentService.getSubmissions('ONBOARDING');

    expect(result).toHaveLength(1001);
    expect(mockedApiClient.get).toHaveBeenNthCalledWith(1, 'v1/recruitment/submissions', {
      params: { status: 'ONBOARDING', skip: 0, limit: 1000 },
    });
    expect(mockedApiClient.get).toHaveBeenNthCalledWith(2, 'v1/recruitment/submissions', {
      params: { status: 'ONBOARDING', skip: 1000, limit: 1000 },
    });
  });

  it('submits through the individual invitation token', async () => {
    mockedApiClient.post.mockResolvedValue({ data: { id: 7 } });

    await recruitmentService.submit('private-token', { email: 'anna@example.com' });

    expect(mockedApiClient.post).toHaveBeenCalledWith(
      'v1/recruitment/submissions/private-token',
      { answers: { email: 'anna@example.com' } },
    );
  });

  it('saves the complete field order in one request', async () => {
    mockedApiClient.put.mockResolvedValue({ data: [] });

    await recruitmentService.reorderFields([3, 1, 2]);

    expect(mockedApiClient.put).toHaveBeenCalledWith('v1/recruitment/fields/order', {
      field_ids: [3, 1, 2],
    });
  });
});
