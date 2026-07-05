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

  it('loads the survey linked to the current account', async () => {
    client.get.mockResolvedValue({ data: { fields: [], interview: null } });

    await departureService.getMine();

    expect(client.get).toHaveBeenCalledWith('v1/recruitment/departures/me');
  });

  it('submits an account-bound departure interview', async () => {
    client.post.mockResolvedValue({ data: { id: 8 } });

    await departureService.submitMine({ departure_date: '2026-06-30' });

    expect(client.post).toHaveBeenCalledWith('v1/recruitment/departures/me', {
      answers: { departure_date: '2026-06-30' },
    });
  });

  it('updates the existing account-bound interview', async () => {
    client.put.mockResolvedValue({ data: { id: 8 } });

    await departureService.updateMine({ departure_reason: 'Nowy powód' });

    expect(client.put).toHaveBeenCalledWith('v1/recruitment/departures/me', {
      answers: { departure_reason: 'Nowy powód' },
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
