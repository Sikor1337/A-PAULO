export type RecruitmentFieldType =
  | 'text'
  | 'textarea'
  | 'email'
  | 'tel'
  | 'date'
  | 'select'
  | 'radio'
  | 'checkbox';

export interface RecruitmentField {
  id: number;
  key: string;
  label: string;
  field_type: RecruitmentFieldType;
  required: boolean;
  placeholder: string;
  options: string[];
  position: number;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface RecruitmentFieldInput {
  label: string;
  field_type: RecruitmentFieldType;
  required: boolean;
  placeholder: string;
  options: string[];
  position?: number;
  is_active?: boolean;
}

export interface RecruitmentForm {
  title: string;
  description: string;
  fields: RecruitmentField[];
}

export interface RecruitmentPublicForm extends RecruitmentForm {
  invitation_token: string;
  recipient_name: string | null;
  recipient_email: string | null;
  return_reason: string | null;
}

export interface RecruitmentInvitationInput {
  recipient_name?: string;
  recipient_email?: string;
}

export interface RecruitmentInvitation {
  id: number;
  token: string;
  recipient_name: string | null;
  recipient_email: string | null;
  is_active: boolean;
  submission_id: number | null;
  submission_status: RecruitmentStatus | null;
  created_at: string;
  updated_at: string;
}

export type RecruitmentStatus = 'SUBMITTED' | 'ONBOARDING' | 'ACCEPTED' | 'REJECTED' | 'RETURNED';

export interface RecruitmentAnswer {
  key: string;
  label: string;
  field_type: RecruitmentFieldType;
  value: unknown;
}

export interface RecruitmentSubmission {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  social_link: string;
  availability: string;
  answers: RecruitmentAnswer[];
  status: RecruitmentStatus;
  return_reason: string | null;
  volunteer_id: number | null;
  submitted_at: string;
  status_changed_at: string;
  created_at: string;
  updated_at: string;
}
