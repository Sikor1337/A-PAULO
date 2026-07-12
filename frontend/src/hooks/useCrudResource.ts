import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errors';
import { appDialog } from '@/lib/appDialog';

interface CrudService<T, TInput> {
  getAll: () => Promise<T[]>;
  create: (data: TInput) => Promise<T>;
  update: (id: number, data: Partial<TInput>) => Promise<T>;
  delete: (id: number) => Promise<void>;
}

interface SaveArgs<TInput> {
  id?: number | null;
  data: TInput;
}

/**
 * Wraps a CRUD service in React Query: list query + save (create/update) + delete mutations,
 * with cache invalidation and error alerts. Keeps React Query out of the UI components.
 */
export function useCrudResource<T, TInput>(
  queryKey: string,
  service: CrudService<T, TInput>,
  options?: { onSaved?: () => void; invalidateKeys?: string[]; enabled?: boolean },
) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: [queryKey] });
    options?.invalidateKeys?.forEach((key) => queryClient.invalidateQueries({ queryKey: [key] }));
  };

  const list = useQuery({
    queryKey: [queryKey],
    queryFn: service.getAll,
    enabled: options?.enabled ?? true,
  });

  const save = useMutation({
    mutationFn: ({ id, data }: SaveArgs<TInput>) =>
      id ? service.update(id, data) : service.create(data),
    onSuccess: () => {
      invalidate();
      options?.onSaved?.();
    },
    onError: (error) => appDialog.error(parseApiError(error)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => service.delete(id),
    onSuccess: invalidate,
    onError: () => appDialog.error('Nie udało się usunąć.'),
  });

  return { data: list.data, isLoading: list.isLoading, save, remove };
}
