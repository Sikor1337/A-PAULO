import { beforeEach, describe, expect, it, vi } from 'vitest';
import apiClient from '@/lib/api';
import { createCrudService } from './crudService';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

interface Item {
  id: number;
  name: string;
}

interface ItemInput {
  name: string;
}

const mockedApiClient = vi.mocked(apiClient);

describe('createCrudService', () => {
  const service = createCrudService<Item, ItemInput>('v1/items');

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('fetches all records from the resource path', async () => {
    const items = [{ id: 1, name: 'Anna' }];
    mockedApiClient.get.mockResolvedValue({ data: items });

    await expect(service.getAll()).resolves.toEqual(items);

    expect(mockedApiClient.get).toHaveBeenCalledWith('v1/items');
  });

  it('fetches a single record by id', async () => {
    const item = { id: 1, name: 'Anna' };
    mockedApiClient.get.mockResolvedValue({ data: item });

    await expect(service.getById(1)).resolves.toEqual(item);

    expect(mockedApiClient.get).toHaveBeenCalledWith('v1/items/1');
  });

  it('creates records with typed payloads', async () => {
    const item = { id: 2, name: 'New item' };
    mockedApiClient.post.mockResolvedValue({ data: item });

    await expect(service.create({ name: 'New item' })).resolves.toEqual(item);

    expect(mockedApiClient.post).toHaveBeenCalledWith('v1/items', { name: 'New item' });
  });

  it('updates records with partial payloads', async () => {
    const item = { id: 2, name: 'Changed item' };
    mockedApiClient.patch.mockResolvedValue({ data: item });

    await expect(service.update(2, { name: 'Changed item' })).resolves.toEqual(item);

    expect(mockedApiClient.patch).toHaveBeenCalledWith('v1/items/2', { name: 'Changed item' });
  });

  it('deletes records by id', async () => {
    mockedApiClient.delete.mockResolvedValue({});

    await expect(service.delete(2)).resolves.toBeUndefined();

    expect(mockedApiClient.delete).toHaveBeenCalledWith('v1/items/2');
  });
});
