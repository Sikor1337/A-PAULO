import type { RecruitmentStatus } from '@/types';

export const recruitmentStatusLabel: Record<RecruitmentStatus, string> = {
  SUBMITTED: 'Nowe zgłoszenie',
  ONBOARDING: 'We wdrażaniu',
  ACCEPTED: 'Wdrożony/a',
  REJECTED: 'Odrzucony/a',
  RETURNED: 'Zwrócony formularz',
};

export const recruitmentStatusClass: Record<RecruitmentStatus, string> = {
  SUBMITTED: 'bg-amber-100 text-amber-800',
  ONBOARDING: 'bg-blue-100 text-blue-800',
  ACCEPTED: 'bg-emerald-100 text-emerald-800',
  REJECTED: 'bg-rose-100 text-rose-800',
  RETURNED: 'bg-violet-100 text-violet-800',
};

export const formatRecruitmentDate = (value: string) =>
  new Intl.DateTimeFormat('pl-PL', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
