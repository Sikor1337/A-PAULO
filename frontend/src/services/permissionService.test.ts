import { beforeEach, describe, expect, it, vi } from 'vitest';
import apiClient from '@/lib/api';
import { permissionService } from './permissionService';

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

describe('permissionService', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('saves the complete group editor state in one request', async () => {
    mockedApiClient.put.mockResolvedValue({ data: { id: 7 } });
    const input = {
      name: 'Reviewer',
      description: 'Reviews data',
      permission_codes: ['CAN_VIEW_USERS', 'CAN_VIEW_SECURITY'] as const,
      user_ids: [3, 5],
    };

    await permissionService.saveGroup(7, {
      ...input,
      permission_codes: [...input.permission_codes],
    });

    expect(mockedApiClient.put).toHaveBeenCalledTimes(1);
    expect(mockedApiClient.put).toHaveBeenCalledWith('v1/security/groups/7', {
      ...input,
      permission_codes: [...input.permission_codes],
    });
  });
});
