import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { departmentService } from '@/services/departmentService';
import { parseApiError } from '@/lib/errors';
import type { DepartmentInput } from '@/types';

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
    onError: (error) => alert(parseApiError(error)),
  });

  const addMember = useMutation({
    mutationFn: ({ id, volunteerId }: { id: number; volunteerId: number }) =>
      departmentService.addMember(id, volunteerId),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  const removeMember = useMutation({
    mutationFn: ({ id, volunteerId }: { id: number; volunteerId: number }) =>
      departmentService.removeMember(id, volunteerId),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  return { save, addMember, removeMember };
}
