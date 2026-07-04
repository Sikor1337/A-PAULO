import type { RecruitmentFieldDraft, RecruitmentFieldType } from './recruitment';

export interface DepartureFieldDraft extends RecruitmentFieldDraft {
  field_type: Exclude<RecruitmentFieldType, 'email' | 'tel'>;
}

export interface DepartureField extends DepartureFieldDraft {
  id: number;
  key: string;
  position: number;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface DepartureAnswer {
  key: string;
  label: string;
  field_type: string;
  value: unknown;
}

export interface DepartureInterview {
  id: number;
  volunteer_id: number;
  departure_date: string;
  departure_reason: string;
  stay_in_contact: boolean;
  answers: DepartureAnswer[];
  completed_by_id: number | null;
  created_at: string;
  updated_at: string;
  volunteer: {
    id: number;
    full_name: string;
    email: string;
  };
}

export interface DepartureSelfService {
  volunteer: DepartureInterview['volunteer'];
  fields: DepartureField[];
  interview: DepartureInterview | null;
}
