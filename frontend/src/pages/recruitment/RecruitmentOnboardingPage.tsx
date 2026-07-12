import { useState } from 'react';
import OnboardingCandidateCards from '@/features/recruitment/OnboardingCandidateCards';
import SubmissionDetailModal from '@/features/recruitment/SubmissionDetailModal';
import SubmissionList from '@/features/recruitment/SubmissionList';
import { useRecruitmentSubmissions } from '@/hooks/useRecruitment';
import { useHasPermission } from '@/hooks/usePermissions';
import { appDialog } from '@/lib/appDialog';
import type { RecruitmentStatus, RecruitmentSubmission } from '@/types';

const tabs: { status: RecruitmentStatus; label: string; empty: string }[] = [
  { status: 'ONBOARDING', label: '3.1 Wdrażanie', empty: 'Obecnie nikt nie jest we wdrażaniu.' },
  { status: 'ACCEPTED', label: '3.2 Wdrożeni', empty: 'Brak wdrożonych osób.' },
  { status: 'REJECTED', label: '3.3 Odrzuceni', empty: 'Brak odrzuconych osób.' },
];

const RecruitmentOnboardingPage = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_RECRUITMENT');
  const [status, setStatus] = useState<RecruitmentStatus>('ONBOARDING');
  const [selected, setSelected] = useState<RecruitmentSubmission | null>(null);
  const [search, setSearch] = useState('');
  const { data = [], isLoading, action, meeting } = useRecruitmentSubmissions(status);
  const currentTab = tabs.find((tab) => tab.status === status)!;
  const normalizedSearch = search.trim().toLocaleLowerCase('pl');
  const filtered = normalizedSearch
    ? data.filter((submission) => (
      submission.full_name.toLocaleLowerCase('pl').includes(normalizedSearch)
      || submission.email.toLocaleLowerCase('pl').includes(normalizedSearch)
      || submission.phone.includes(normalizedSearch)
    ))
    : data;

  const returnSubmission = async (submission: RecruitmentSubmission) => {
    const note = await appDialog.prompt('Co kandydat ma poprawić?', { title: 'Zwróć formularz', confirmLabel: 'Zwróć' });
    if (note === null) return;
    action.mutate({ id: submission.id, action: 'return', note });
  };

  const decide = async (submission: RecruitmentSubmission, nextAction: 'accept' | 'reject') => {
    const label = nextAction === 'accept' ? 'wdrożenia' : 'odrzucenia';
    const note = await appDialog.prompt(`Komentarz do ${label} (opcjonalnie):`, { title: 'Decyzja rekrutacyjna' });
    if (note === null) return;
    action.mutate({ id: submission.id, action: nextAction, note });
  };

  const restore = async (submission: RecruitmentSubmission) => {
    if (!await appDialog.confirm(`Cofnąć ${submission.full_name} do etapu wdrażania?`, { title: 'Przywróć kandydata' })) return;
    action.mutate({ id: submission.id, action: 'restore-onboarding' });
  };

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-900">Wdrażanie wolontariuszy</h2>
        <p className="text-sm text-gray-500">Zaznacz obecność na czterech wymaganych spotkaniach. Data zapisze się automatycznie.</p>
      </div>
      <div className="mb-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
        {tabs.map((tab) => (
          <button key={tab.status} onClick={() => setStatus(tab.status)} className={`rounded-xl border px-4 py-3 text-sm font-bold transition-colors ${status === tab.status ? 'border-indigo-600 bg-indigo-600 text-white' : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'}`}>{tab.label}</button>
        ))}
      </div>
      <label className="mb-4 block">
        <span className="sr-only">Szukaj kandydata</span>
        <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Szukaj po imieniu, e-mailu lub telefonie…" className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
      </label>

      {status === 'ONBOARDING' ? (
        <OnboardingCandidateCards
          submissions={filtered}
          canManage={canManage}
          isLoading={isLoading}
          pendingMeeting={meeting.isPending ? meeting.variables : undefined}
          onAttendanceChange={(submission, meetingType, attended) => meeting.mutate({ id: submission.id, meetingType, attended })}
          onDetails={setSelected}
          onPromote={(submission) => decide(submission, 'accept')}
          onReject={(submission) => decide(submission, 'reject')}
          onReturn={returnSubmission}
        />
      ) : (
        <SubmissionList
          submissions={filtered}
          isLoading={isLoading}
          emptyText={currentTab.empty}
          onSelect={setSelected}
          actions={canManage ? (submission) => (
            <button onClick={() => restore(submission)} className="rounded-lg bg-blue-50 px-3 py-2 text-xs font-bold text-blue-700">Cofnij do wdrażania</button>
          ) : undefined}
        />
      )}
      {selected && <SubmissionDetailModal submission={selected} onClose={() => setSelected(null)} />}
    </section>
  );
};

export default RecruitmentOnboardingPage;
