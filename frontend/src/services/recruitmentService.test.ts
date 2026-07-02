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

  it('submits through the account-bound permanent form', async () => {
    mockedApiClient.post.mockResolvedValue({ data: { id: 7 } });

    await recruitmentService.submit({ email: 'anna@example.com' }, 'token-123');

    expect(mockedApiClient.post).toHaveBeenCalledWith(
      'v1/recruitment/submissions',
      { answers: { email: 'anna@example.com' } },
      { headers: { 'X-Recruitment-Token': 'token-123' } },
    );
  });

  it('loads the opaque recruitment path from the backend', async () => {
    mockedApiClient.get.mockResolvedValue({ data: { path: '/recrutation/abc' } });

    await expect(recruitmentService.getAccessLink()).resolves.toBe('/recrutation/abc');
    expect(mockedApiClient.get).toHaveBeenCalledWith('v1/recruitment/access-link');
  });

  it('saves the complete form draft in one request', async () => {
    mockedApiClient.put.mockResolvedValue({ data: [] });

    const fields = [{
      id: 3,
      label: 'Obszary',
      field_type: 'multiselect' as const,
      required: true,
      placeholder: '',
      options: ['Seniorzy', 'Dzieci'],
      is_active: true,
    }];
    await recruitmentService.saveFields(fields);

    expect(mockedApiClient.put).toHaveBeenCalledWith('v1/recruitment/fields', { fields });
  });

  it('records onboarding attendance in one request', async () => {
    mockedApiClient.put.mockResolvedValue({ data: { id: 7 } });

    await recruitmentService.setOnboardingAttendance(7, 'COMMUNITY', true);

    expect(mockedApiClient.put).toHaveBeenCalledWith(
      'v1/recruitment/submissions/7/onboarding-meetings/COMMUNITY',
      { attended: true },
    );
  });
});
