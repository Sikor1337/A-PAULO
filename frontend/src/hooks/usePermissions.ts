import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errors';
import { permissionService } from '@/services/permissionService';
import { useAuthStore } from '@/stores/authStore';
import type { PermissionCode, SecurityGroupInput } from '@/types';

export function useMyPermissions() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return useQuery({
    queryKey: ['my-permissions'],
    queryFn: permissionService.getMine,
    enabled: isAuthenticated,
    staleTime: 60_000,
  });
}

export function useHasPermission(permission: PermissionCode) {
  const query = useMyPermissions();
  return {
    ...query,
    hasPermission: query.data?.permissions.includes(permission) ?? false,
  };
}

export function useSecurityGroups(enabled = true) {
  const queryClient = useQueryClient();
  const permissions = useQuery({
    queryKey: ['security-permissions'],
    queryFn: permissionService.getPermissions,
    enabled,
  });
  const groups = useQuery({
    queryKey: ['security-groups'],
    queryFn: permissionService.getGroups,
    enabled,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['security-groups'] });
    queryClient.invalidateQueries({ queryKey: ['my-permissions'] });
  };
  const onError = (error: unknown) => alert(parseApiError(error, 'Nie udało się zapisać uprawnień.'));

  const create = useMutation({
    mutationFn: (input: SecurityGroupInput) => permissionService.createGroup(input),
    onSuccess: refresh,
    onError,
  });
  const update = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Pick<SecurityGroupInput, 'name' | 'description'> }) =>
      permissionService.updateGroup(id, input),
    onSuccess: refresh,
    onError,
  });
  const setPermissions = useMutation({
    mutationFn: ({ id, codes }: { id: number; codes: PermissionCode[] }) =>
      permissionService.setGroupPermissions(id, codes),
    onSuccess: refresh,
    onError,
  });
  const setUsers = useMutation({
    mutationFn: ({ id, userIds }: { id: number; userIds: number[] }) =>
      permissionService.setGroupUsers(id, userIds),
    onSuccess: refresh,
    onError,
  });
  const remove = useMutation({
    mutationFn: permissionService.deleteGroup,
    onSuccess: refresh,
    onError,
  });

  return { permissions, groups, create, update, setPermissions, setUsers, remove };
}
