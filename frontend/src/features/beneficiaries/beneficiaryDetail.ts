import type { DetailField } from '@/components/ui/DetailModal';
import type { Beneficiary } from '@/types';

/** Field list for the beneficiary details modal. Shared by BeneficiariesPage and GroupsPage. */
export function beneficiaryDetailFields(b: Beneficiary): DetailField[] {
  return [
    { label: 'Adres', value: b.address },
    { label: 'Grupa', value: b.group_name },
    { label: 'Telefon', value: b.phone },
    { label: 'Telefon rodziny', value: b.family_phone },
    { label: 'Status', value: b.status },
    { label: 'BO', value: b.bo_enrolled ? 'Tak' : 'Nie' },
    { label: 'Opis / Notatki', value: b.description },
    { label: 'Ostatnia wizyta księdza', value: b.last_priest_visit },
    { label: 'Ostatnie spotkanie z wol.', value: b.last_volunteer_meeting },
    { label: 'Historia', value: b.history },
  ];
}
