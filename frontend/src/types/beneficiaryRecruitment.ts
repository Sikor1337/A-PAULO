import type { RecruitmentAnswer, RecruitmentField, RecruitmentFieldDraft } from './recruitment';

export type BeneficiaryRecruitmentStatus = 'NEW' | 'BENEFICIARY_CREATED' | 'REJECTED' | 'ARCHIVED';

export interface BeneficiaryRecruitmentForm {
  title: string;
  description: string;
  fields: RecruitmentField[];
  form_token: string;
}

export interface BeneficiaryRecruitmentSubmission {
  id: number;
  full_name: string;
  address: string;
  phone: string | null;
  reporter_name: string;
  reporter_phone: string;
  help_needed: string;
  answers: RecruitmentAnswer[];
  status: BeneficiaryRecruitmentStatus;
  decision_comment: string | null;
  beneficiary_id: number | null;
  submitted_at: string;
  archived_at: string | null;
  updated_at: string;
}

export type BeneficiaryRecruitmentFieldDraft = RecruitmentFieldDraft;
