import { useQuery } from '@tanstack/react-query';
import { useCrudResource } from './useCrudResource';
import { roleService } from '@/services/roleService';
import type { Role, RoleInput } from '@/types';

/** Full CRUD resource for roles (list + save + delete). */
export function useRoles(options?: { onSaved?: () => void }) {
  return useCrudResource<Role, RoleInput>('roles', roleService, {
    onSaved: options?.onSaved,
    invalidateKeys: ['volunteers'],
  });
}

/** Read-only role list, for screens that only need lookup data (e.g. the volunteer form). */
export function useRoleList() {
  return useQuery({ queryKey: ['roles'], queryFn: roleService.getAll });
}
