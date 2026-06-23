export type VolunteerStatus = 'Aktywny' | 'Były';

export interface VolunteerFunction {
  id: number;
  name: string;
  is_system: boolean;
  is_active: boolean;
}

export interface VolunteerFunctionInput {
  name: string;
}

/** Volunteer as returned by VolunteerSerializer (backend/volunteers/serializers.py). */
export interface Volunteer {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  social_link: string | null;
  function_ids: number[];
  manual_functions: string[];
  derived_functions: string[];
  functions: string[];
  status: VolunteerStatus;
  join_date: string | null;
  notes: string | null;
  history: string | null;
  // Computed, read-only:
  led_group: string | null;
  /** Comma-joined group names, e.g. "GRUPA A, GRUPA B". */
  assigned_groups: string | null;
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
  function_ids?: number[];
  status: VolunteerStatus;
  join_date: string;
  notes?: string;
  history?: string;
}
