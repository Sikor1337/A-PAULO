export type VolunteerStatus = 'Aktywny' | 'Były';

/** Volunteer as returned by VolunteerSerializer (backend/volunteers/serializers.py). */
export interface Volunteer {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  social_link: string | null;
  status: VolunteerStatus;
  join_date: string | null;
  notes: string | null;
  history: string | null;
  // Computed, read-only:
  led_group: string | null;
  /** Comma-joined group names, e.g. "GRUPA A, GRUPA B". */
  assigned_groups: string;
  main_for_beneficiaries: string[];
  created_at: string;
  updated_at: string;
}

/** Writable payload for creating/updating a volunteer. */
export interface VolunteerInput {
  full_name: string;
  email: string;
  phone: string;
  social_link?: string;
  status: VolunteerStatus;
  join_date: string;
  notes?: string;
  history?: string;
}
