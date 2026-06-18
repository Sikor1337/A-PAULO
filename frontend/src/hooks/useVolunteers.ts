import { useQuery } from '@tanstack/react-query';
import { useCrudResource } from './useCrudResource';
import { volunteerService } from '@/services/volunteerService';
import type { Volunteer, VolunteerInput } from '@/types';

/** Full CRUD resource for volunteers (list + save + delete). */
export function useVolunteers(options?: { onSaved?: () => void }) {
  return useCrudResource<Volunteer, VolunteerInput>('volunteers', volunteerService, {
    onSaved: options?.onSaved,
    invalidateKeys: ['groups', 'group-detail'],
  });
}

/** Read-only volunteer list, for screens that only need lookup data (e.g. Groups). */
export function useVolunteerList() {
  return useQuery({ queryKey: ['volunteers'], queryFn: volunteerService.getAll });
}
