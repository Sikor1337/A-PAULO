import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { taskService } from '@/services/taskService';
import { parseApiError } from '@/lib/errors';
import type { TaskCreateInput, TaskFilters, TaskUpdateInput } from '@/types';

/** Task list with server-side filters. */
export function useTaskList(filters: Partial<TaskFilters>) {
  return useQuery({
    queryKey: ['tasks', filters],
    queryFn: () => taskService.list(filters),
  });
}

/** Create / update / delete tasks and manage checklist items. */
export function useTaskActions(options?: { onSaved?: () => void }) {
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['tasks'] });
  const onError = (error: unknown) => alert(parseApiError(error));

  const save = useMutation({
    mutationFn: ({ id, data }: { id?: number | null; data: TaskCreateInput | TaskUpdateInput }) =>
      id ? taskService.update(id, data as TaskUpdateInput) : taskService.create(data as TaskCreateInput),
    onSuccess: () => {
      invalidate();
      options?.onSaved?.();
    },
    onError,
  });

  const remove = useMutation({
    mutationFn: (id: number) => taskService.delete(id),
    onSuccess: invalidate,
    onError,
  });

  const addItem = useMutation({
    mutationFn: ({ taskId, label }: { taskId: number; label: string }) =>
      taskService.addChecklistItem(taskId, label),
    onSuccess: invalidate,
    onError,
  });

  const updateItem = useMutation({
    mutationFn: ({
      taskId,
      itemId,
      data,
    }: {
      taskId: number;
      itemId: number;
      data: { label?: string; is_done?: boolean; volunteer_id?: number; clear_volunteer?: boolean };
    }) => taskService.updateChecklistItem(taskId, itemId, data),
    onSuccess: invalidate,
    onError,
  });

  const removeItem = useMutation({
    mutationFn: ({ taskId, itemId }: { taskId: number; itemId: number }) =>
      taskService.deleteChecklistItem(taskId, itemId),
    onSuccess: invalidate,
    onError,
  });

  return { save, remove, addItem, updateItem, removeItem };
}
