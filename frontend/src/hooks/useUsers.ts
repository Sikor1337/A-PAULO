import { useCrudResource } from './useCrudResource';
import { userService } from '@/services/userService';
import type { AdminUser, AdminUserInput } from '@/types';

export function useUsers(options?: { onSaved?: () => void }) {
  return useCrudResource<AdminUser, AdminUserInput>('users', userService, {
    onSaved: options?.onSaved,
  });
}
