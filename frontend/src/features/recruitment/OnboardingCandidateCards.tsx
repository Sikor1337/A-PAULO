import type { OnboardingMeetingType, RecruitmentSubmission } from '@/types';

const onboardingMeetings: ReadonlyArray<{ type: OnboardingMeetingType; label: string }> = [
  { type: 'CHARISM', label: 'Charyzmat' },
  { type: 'COMMUNITY', label: 'Wspólnota' },
  { type: 'ADMINISTRATION', label: 'Administracja' },
  { type: 'ACTIVITY', label: 'Działanie' },
];

const formatAttendanceDate = (value: string) => new Intl.DateTimeFormat('pl-PL', {
  day: '2-digit', month: '2-digit', year: 'numeric',
}).format(new Date(value));

const completedMeetingsCount = (submission: RecruitmentSubmission) => (
  onboardingMeetings.filter(({ type }) => (submission.onboarding_meetings ?? []).some(
    (meeting) => meeting.meeting_type === type && meeting.attended_at !== null,
  )).length
);

interface Props {
  submissions: RecruitmentSubmission[];
  canManage: boolean;
  isLoading: boolean;
  pendingMeeting?: { id: number; meetingType: OnboardingMeetingType };
  onAttendanceChange: (submission: RecruitmentSubmission, meetingType: OnboardingMeetingType, attended: boolean) => void;
  onDetails: (submission: RecruitmentSubmission) => void;
  onPromote: (submission: RecruitmentSubmission) => void;
  onReject: (submission: RecruitmentSubmission) => void;
  onReturn: (submission: RecruitmentSubmission) => void;
}

const OnboardingCandidateCards = ({
  submissions, canManage, isLoading, pendingMeeting,
  onAttendanceChange, onDetails, onPromote, onReject, onReturn,
}: Props) => {
  if (isLoading) return <div className="rounded-xl border border-gray-200 p-10 text-center text-gray-400">Ładowanie…</div>;
  if (!submissions.length) return <div className="rounded-xl border border-dashed border-gray-300 p-10 text-center text-gray-500">Obecnie nikt nie jest we wdrażaniu.</div>;

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {submissions.map((submission) => {
        const completed = completedMeetingsCount(submission);
        const isComplete = completed === onboardingMeetings.length;
        return (
          <article key={submission.id} className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-100 p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <button type="button" onClick={() => onDetails(submission)} className="text-left text-lg font-black text-gray-900 hover:text-indigo-600">{submission.full_name}</button>
                  <p className="mt-1 truncate text-sm text-gray-600">{submission.email}</p>
                  <p className="text-sm text-gray-500">{submission.phone}</p>
                </div>
                <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold ${isComplete ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                  {isComplete ? 'Gotowy do promocji' : `${completed}/4 spotkania`}
                </span>
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-gray-100" aria-label={`Postęp wdrażania ${completed} z 4`}>
                <div className="h-full rounded-full bg-indigo-600 transition-all" style={{ width: `${completed * 25}%` }} />
              </div>
            </div>

            <fieldset className="space-y-2 p-5">
              <legend className="mb-3 text-sm font-black text-gray-900">Obecność na spotkaniach wdrożeniowych</legend>
              {onboardingMeetings.map(({ type, label }) => {
                const attendance = (submission.onboarding_meetings ?? []).find((meeting) => meeting.meeting_type === type);
                const attended = attendance?.attended_at != null;
                const pending = pendingMeeting?.id === submission.id && pendingMeeting.meetingType === type;
                return (
                  <label key={type} className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 transition-colors ${attended ? 'border-emerald-200 bg-emerald-50' : 'border-gray-200 bg-gray-50'} ${!canManage || pending ? 'cursor-default opacity-70' : 'hover:border-indigo-300'}`}>
                    <input type="checkbox" checked={attended} disabled={!canManage || pending} onChange={(event) => onAttendanceChange(submission, type, event.target.checked)} className="h-5 w-5 shrink-0 accent-indigo-600" />
                    <span className="min-w-0 flex-1 text-sm font-bold text-gray-800">{label}</span>
                    <span className={`shrink-0 text-xs font-semibold ${attended ? 'text-emerald-700' : 'text-gray-400'}`}>
                      {pending ? 'Zapisywanie…' : attendance?.attended_at ? formatAttendanceDate(attendance.attended_at) : 'Brak obecności'}
                    </span>
                  </label>
                );
              })}
            </fieldset>

            <div className="flex flex-wrap gap-2 border-t border-gray-100 bg-gray-50 p-4">
              <button type="button" onClick={() => onDetails(submission)} className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-700">Odpowiedzi</button>
              {canManage && <>
                <button type="button" onClick={() => onPromote(submission)} disabled={!isComplete} title={isComplete ? 'Promuj do wolontariusza' : 'Wymagane są wszystkie 4 spotkania'} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:bg-gray-300">Promuj do wolontariusza</button>
                <button type="button" onClick={() => onReject(submission)} className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">Odrzuć</button>
                <button type="button" onClick={() => onReturn(submission)} className="rounded-lg bg-violet-50 px-3 py-2 text-xs font-bold text-violet-700">Zwróć formularz</button>
              </>}
            </div>
          </article>
        );
      })}
    </div>
  );
};

export default OnboardingCandidateCards;
