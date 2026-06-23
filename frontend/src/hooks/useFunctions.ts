import { useQuery } from '@tanstack/react-query';
import { useCrudResource } from './useCrudResource';
import { functionService } from '@/services/functionService';
import type { VolunteerFunction, VolunteerFunctionInput } from '@/types';

/** Full CRUD resource for the volunteer function catalog. */
export function useFunctions(options?: { onSaved?: () => void }) {
  return useCrudResource<VolunteerFunction, VolunteerFunctionInput>('functions', functionService, {
    onSaved: options?.onSaved,
    invalidateKeys: ['volunteers'],
  });
}

/** Read-only function list for assignment controls. */
export function useFunctionList() {
  return useQuery({ queryKey: ['functions'], queryFn: functionService.getAll });
}
