import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { RecruitmentSubmission } from '@/types';
import OnboardingCandidateCards from './OnboardingCandidateCards';

const submission: RecruitmentSubmission = {
  id: 7,
  user_id: 17,
  full_name: 'Anna Kowalska',
  email: 'anna@example.com',
  phone: '123456789',
  social_link: '',
  availability: '',
  answers: [],
  status: 'ONBOARDING',
  return_reason: null,
  decision_comment: null,
  volunteer_id: null,
  onboarding_meetings: [
    { meeting_type: 'CHARISM', attended_at: '2026-07-02T10:00:00Z' },
    { meeting_type: 'COMMUNITY', attended_at: '2026-07-02T10:00:00Z' },
    { meeting_type: 'ADMINISTRATION', attended_at: '2026-07-02T10:00:00Z' },
    { meeting_type: 'ACTIVITY', attended_at: null },
  ],
  submitted_at: '2026-06-30T10:00:00Z',
  status_changed_at: '2026-07-01T10:00:00Z',
  created_at: '2026-06-30T10:00:00Z',
  updated_at: '2026-07-02T10:00:00Z',
};

const props = {
  submissions: [submission],
  canManage: true,
  isLoading: false,
  onAttendanceChange: vi.fn(),
  onDetails: vi.fn(),
  onPromote: vi.fn(),
  onReject: vi.fn(),
  onReturn: vi.fn(),
};

describe('OnboardingCandidateCards', () => {
  it('shows dates and blocks promotion until all meetings are completed', () => {
    const { rerender } = render(<OnboardingCandidateCards {...props} />);

    expect(screen.getByText('3/4 spotkania')).toBeInTheDocument();
    expect(screen.getAllByText('02.07.2026')).toHaveLength(3);
    expect(screen.getByRole('button', { name: 'Promuj do wolontariusza' })).toBeDisabled();

    rerender(<OnboardingCandidateCards
      {...props}
      submissions={[{
        ...submission,
        onboarding_meetings: submission.onboarding_meetings.map((meeting) => ({
          ...meeting,
          attended_at: meeting.attended_at ?? '2026-07-02T11:00:00Z',
        })),
      }]}
    />);

    expect(screen.getByText('Gotowy do promocji')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Promuj do wolontariusza' })).toBeEnabled();
  });

  it('reports the selected attendance change', () => {
    const onAttendanceChange = vi.fn();
    render(<OnboardingCandidateCards {...props} onAttendanceChange={onAttendanceChange} />);

    fireEvent.click(screen.getByRole('checkbox', { name: /Działanie/ }));

    expect(onAttendanceChange).toHaveBeenCalledWith(submission, 'ACTIVITY', true);
  });
});
