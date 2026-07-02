export type RecruitmentFieldType =
  | 'text'
  | 'textarea'
  | 'email'
  | 'tel'
  | 'date'
  | 'select'
  | 'radio'
  | 'multiselect'
  | 'checkbox';

export interface RecruitmentFieldDraft {
  id?: number;
  is_system?: boolean;
  label: string;
  field_type: RecruitmentFieldType;
  required: boolean;
  placeholder: string;
  options: string[];
  is_active: boolean;
}

export interface RecruitmentField extends RecruitmentFieldDraft {
  id: number;
  key: string;
  position: number;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface RecruitmentForm {
  title: string;
  description: string;
  fields: RecruitmentField[];
  applicant_name: string;
  applicant_email: string;
  initial_answers: Record<string, unknown>;
  submission_status: RecruitmentStatus | null;
  return_reason: string | null;
}

export type RecruitmentStatus = 'SUBMITTED' | 'ONBOARDING' | 'ACCEPTED' | 'REJECTED' | 'RETURNED';
export type OnboardingMeetingType = 'CHARISM' | 'COMMUNITY' | 'ADMINISTRATION' | 'ACTIVITY';

export interface RecruitmentOnboardingMeeting {
  meeting_type: OnboardingMeetingType;
  attended_at: string | null;
}

export interface RecruitmentAnswer {
  key: string;
  label: string;
  field_type: RecruitmentFieldType;
  value: unknown;
}

export interface RecruitmentSubmission {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  phone: string;
  social_link: string;
  availability: string;
  answers: RecruitmentAnswer[];
  status: RecruitmentStatus;
  return_reason: string | null;
  decision_comment: string | null;
  volunteer_id: number | null;
  onboarding_meetings: RecruitmentOnboardingMeeting[];
  submitted_at: string;
  status_changed_at: string;
  created_at: string;
  updated_at: string;
}
