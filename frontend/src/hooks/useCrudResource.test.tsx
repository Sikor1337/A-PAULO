import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useCrudResource } from './useCrudResource';
import { appDialog } from '@/lib/appDialog';

interface Item {
  id: number;
  name: string;
}

interface ItemInput {
  name: string;
}

const createService = () => ({
  getAll: vi.fn<() => Promise<Item[]>>(),
  create: vi.fn<(data: ItemInput) => Promise<Item>>(),
  update: vi.fn<(id: number, data: Partial<ItemInput>) => Promise<Item>>(),
  delete: vi.fn<(id: number) => Promise<void>>(),
});

describe('useCrudResource', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('loads resource data through React Query', async () => {
    const service = createService();
    const items = [{ id: 1, name: 'Anna' }];
    service.getAll.mockResolvedValue(items);

    const { result } = renderHook(() => useCrudResource<Item, ItemInput>('items', service), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(service.getAll).toHaveBeenCalledOnce();
    expect(result.current.data).toEqual(items);
  });

  it('creates new records and invalidates related queries', async () => {
    const service = createService();
    const onSaved = vi.fn();
    const invalidateQueries = vi.spyOn(queryClient, 'invalidateQueries');
    service.getAll.mockResolvedValue([]);
    service.create.mockResolvedValue({ id: 2, name: 'New item' });

    const { result } = renderHook(
      () =>
        useCrudResource<Item, ItemInput>('items', service, {
          onSaved,
          invalidateKeys: ['groups'],
        }),
      { wrapper },
    );

    await act(async () => {
      await result.current.save.mutateAsync({ data: { name: 'New item' } });
    });

    expect(service.create).toHaveBeenCalledWith({ name: 'New item' });
    expect(service.update).not.toHaveBeenCalled();
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ['items'] });
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ['groups'] });
    expect(onSaved).toHaveBeenCalledOnce();
  });

  it('updates existing records when an id is provided', async () => {
    const service = createService();
    service.getAll.mockResolvedValue([]);
    service.update.mockResolvedValue({ id: 7, name: 'Changed item' });

    const { result } = renderHook(() => useCrudResource<Item, ItemInput>('items', service), { wrapper });

    await act(async () => {
      await result.current.save.mutateAsync({ id: 7, data: { name: 'Changed item' } });
    });

    expect(service.update).toHaveBeenCalledWith(7, { name: 'Changed item' });
    expect(service.create).not.toHaveBeenCalled();
  });

  it('alerts when deleting a record fails', async () => {
    const service = createService();
    const alert = vi.spyOn(appDialog, 'error').mockImplementation(() => undefined);
    service.getAll.mockResolvedValue([]);
    service.delete.mockRejectedValue(new Error('boom'));

    const { result } = renderHook(() => useCrudResource<Item, ItemInput>('items', service), { wrapper });

    await expect(result.current.remove.mutateAsync(7)).rejects.toThrow('boom');

    expect(service.delete).toHaveBeenCalledWith(7);
    expect(alert).toHaveBeenCalledWith('Nie uda\u0142o si\u0119 usun\u0105\u0107.');
  });
});
