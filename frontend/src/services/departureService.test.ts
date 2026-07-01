import { beforeEach, describe, expect, it, vi } from 'vitest';
import apiClient from '@/lib/api';
import { departureService } from './departureService';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const client = vi.mocked(apiClient);

describe('departureService', () => {
  beforeEach(() => vi.resetAllMocks());

  it('creates an account-bound departure interview', async () => {
    client.post.mockResolvedValue({ data: { id: 8 } });

    await departureService.create(4, { departure_date: '2026-06-30' });

    expect(client.post).toHaveBeenCalledWith('v1/recruitment/departures', {
      volunteer_id: 4,
      answers: { departure_date: '2026-06-30' },
    });
  });

  it('loads all departure interviews for the history view', async () => {
    client.get.mockResolvedValue({ data: [] });

    await departureService.getAll();

    expect(client.get).toHaveBeenCalledWith('v1/recruitment/departures', {
      params: { skip: 0, limit: 1000 },
    });
  });
});
