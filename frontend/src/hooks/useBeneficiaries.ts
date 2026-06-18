import { useQuery } from '@tanstack/react-query';
import { useCrudResource } from './useCrudResource';
import { beneficiaryService } from '@/services/beneficiaryService';
import type { Beneficiary, BeneficiaryInput } from '@/types';

/** Full CRUD resource for beneficiaries (list + save + delete). */
export function useBeneficiaries(options?: { onSaved?: () => void }) {
  return useCrudResource<Beneficiary, BeneficiaryInput>('beneficiaries', beneficiaryService, {
    onSaved: options?.onSaved,
    invalidateKeys: ['groups', 'group-detail'],
  });
}

/** Read-only beneficiary list, for screens that only need lookup data (e.g. Groups). */
export function useBeneficiaryList() {
  return useQuery({ queryKey: ['beneficiaries'], queryFn: beneficiaryService.getAll });
}
