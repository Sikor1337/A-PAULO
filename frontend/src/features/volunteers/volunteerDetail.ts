import type { DetailField } from '@/components/ui/DetailModal';
import { formatDate } from '@/lib/date';
import type { Volunteer } from '@/types';

/** Field list for the volunteer details modal. Shared by VolunteersPage and GroupsPage. */
export function volunteerDetailFields(v: Volunteer): DetailField[] {
  return [
    { label: 'Email', value: v.email },
    { label: 'Rola', value: v.role_name },
    { label: 'Lider Grupy', value: v.led_group },
    { label: 'Członek Grup', value: v.assigned_groups },
    { label: 'Główny wolontariusz dla', value: v.main_for_beneficiaries?.join(', ') },
    { label: 'Telefon', value: v.phone },
    { label: 'Profil społecznościowy', value: v.social_link },
    { label: 'Status', value: v.status },
    { label: 'Data przystąpienia', value: formatDate(v.join_date) },
    { label: 'Notatki', value: v.notes },
    { label: 'Historia', value: v.history },
  ];
}
