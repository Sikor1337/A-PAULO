import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errors';
import { appDialog } from '@/lib/appDialog';
import { permissionService } from '@/services/permissionService';
import { useAuthStore } from '@/stores/authStore';
import type { PermissionCode, SecurityGroupInput, SecurityGroupSaveInput } from '@/types';

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
  const onError = (error: unknown) => appDialog.error(parseApiError(error, 'Nie udało się zapisać uprawnień.'));

  const create = useMutation({
    mutationFn: (input: SecurityGroupInput) => permissionService.createGroup(input),
    onSuccess: refresh,
    onError,
  });
  const save = useMutation({
    mutationFn: ({ id, input }: { id: number; input: SecurityGroupSaveInput }) =>
      permissionService.saveGroup(id, input),
    onSuccess: refresh,
    onError,
  });
  const remove = useMutation({
    mutationFn: permissionService.deleteGroup,
    onSuccess: refresh,
    onError,
  });

  return { permissions, groups, create, save, remove };
}
