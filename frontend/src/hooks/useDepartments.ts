import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { departmentService } from '@/services/departmentService';
import { parseApiError } from '@/lib/errors';
import { appDialog } from '@/lib/appDialog';
import type { DepartmentInput, DepartmentInventoryItemInput } from '@/types';

/** Department list (optionally with archived ones). */
export function useDepartmentList(includeArchived = false) {
  return useQuery({
    queryKey: ['departments', { includeArchived }],
    queryFn: () => departmentService.list(includeArchived),
  });
}

/** Single department with members. */
export function useDepartmentDetail(id: number | null) {
  return useQuery({
    queryKey: ['department-detail', id],
    queryFn: () => departmentService.get(id as number),
    enabled: id !== null,
  });
}

export function useDepartmentInventory(id: number | null) {
  return useQuery({
    queryKey: ['department-inventory', id],
    queryFn: () => departmentService.getInventory(id as number),
    enabled: id !== null,
  });
}

/** Create/update/archive departments and manage their members. */
export function useDepartmentActions(options?: { onSaved?: () => void }) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['departments'] });
    queryClient.invalidateQueries({ queryKey: ['department-detail'] });
  };

  const save = useMutation({
    mutationFn: ({ id, data }: { id?: number | null; data: Partial<DepartmentInput> & { is_archived?: boolean } }) =>
      id
        ? departmentService.update(id, data)
        : departmentService.create(data as DepartmentInput),
    onSuccess: () => {
      invalidate();
      options?.onSaved?.();
    },
    onError: (error) => appDialog.error(parseApiError(error)),
  });

  const addMember = useMutation({
    mutationFn: ({ id, volunteerId }: { id: number; volunteerId: number }) =>
      departmentService.addMember(id, volunteerId),
    onSuccess: invalidate,
    onError: (error) => appDialog.error(parseApiError(error)),
  });

  const removeMember = useMutation({
    mutationFn: ({ id, volunteerId }: { id: number; volunteerId: number }) =>
      departmentService.removeMember(id, volunteerId),
    onSuccess: invalidate,
    onError: (error) => appDialog.error(parseApiError(error)),
  });

  const join = useMutation({
    mutationFn: (id: number) => departmentService.join(id),
    onSuccess: invalidate,
    onError: (error) => appDialog.error(parseApiError(error)),
  });

  const approveMember = useMutation({
    mutationFn: ({ id, volunteerId }: { id: number; volunteerId: number }) =>
      departmentService.approveMember(id, volunteerId),
    onSuccess: invalidate,
    onError: (error) => appDialog.error(parseApiError(error)),
  });

  const leave = useMutation({
    mutationFn: (id: number) => departmentService.leave(id),
    onSuccess: invalidate,
    onError: (error) => appDialog.error(parseApiError(error)),
  });

  return { save, addMember, removeMember, join, approveMember, leave };
}

export function useDepartmentInventoryActions() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['department-inventory'] });
  const onError = (error: unknown) => appDialog.error(parseApiError(error));

  const save = useMutation({
    mutationFn: ({
      departmentId,
      itemId,
      data,
    }: {
      departmentId: number;
      itemId?: number;
      data: DepartmentInventoryItemInput;
    }) => itemId
      ? departmentService.updateInventoryItem(departmentId, itemId, data)
      : departmentService.createInventoryItem(departmentId, data),
    onSuccess: invalidate,
    onError,
  });
  const remove = useMutation({
    mutationFn: ({ departmentId, itemId }: { departmentId: number; itemId: number }) =>
      departmentService.deleteInventoryItem(departmentId, itemId),
    onSuccess: invalidate,
    onError,
  });
  return { save, remove };
}
