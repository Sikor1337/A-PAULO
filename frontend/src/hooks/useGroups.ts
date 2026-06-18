import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { groupService } from '@/services/groupService';
import { parseApiError } from '@/lib/errors';
import type { GroupListItem, GroupDetail, GroupSaveInput } from '@/types';

const invalidateKeys = ['groups', 'beneficiaries', 'group-detail'];

/** Group list, detail, and save/delete mutations. UI side-effects are passed at the call site. */
export function useGroups() {
  const queryClient = useQueryClient();
  const invalidate = () => invalidateKeys.forEach((key) => queryClient.invalidateQueries({ queryKey: [key] }));

  const list = useQuery({ queryKey: ['groups'], queryFn: groupService.getAll });

  const saveGroup = useMutation({
    mutationFn: ({ id, data }: { id: number | null; data: GroupSaveInput }) =>
      id ? groupService.update(id, data) : groupService.create(data),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  const deleteGroup = useMutation({
    mutationFn: (id: number) => groupService.delete(id),
    onSuccess: invalidate,
    onError: () => alert('Nie udało się usunąć grupy.'),
  });

  return { groups: list.data as GroupListItem[] | undefined, saveGroup, deleteGroup };
}

/** Read-only group list, for filter dropdowns on other pages. */
export function useGroupList() {
  return useQuery<GroupListItem[]>({ queryKey: ['groups'], queryFn: groupService.getAll });
}

/** Detail query for a single group, enabled only when an id is selected. */
export function useGroupDetail(id: number | null) {
  return useQuery<GroupDetail>({
    queryKey: ['group-detail', id],
    queryFn: () => groupService.getById(id as number),
    enabled: id !== null,
  });
}
