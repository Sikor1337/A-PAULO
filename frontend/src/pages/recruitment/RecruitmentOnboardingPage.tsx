import { useState } from 'react';
import SubmissionDetailModal from '@/features/recruitment/SubmissionDetailModal';
import SubmissionList from '@/features/recruitment/SubmissionList';
import { useRecruitmentSubmissions } from '@/hooks/useRecruitment';
import type { RecruitmentStatus, RecruitmentSubmission } from '@/types';

const tabs: { status: RecruitmentStatus; label: string; empty: string }[] = [
  { status: 'ONBOARDING', label: '3.1 Wdrażanie', empty: 'Obecnie nikt nie jest we wdrażaniu.' },
  { status: 'ACCEPTED', label: '3.2 Wdrożeni', empty: 'Brak wdrożonych osób.' },
  { status: 'REJECTED', label: '3.3 Odrzuceni', empty: 'Brak odrzuconych osób.' },
];

const RecruitmentOnboardingPage = () => {
  const [status, setStatus] = useState<RecruitmentStatus>('ONBOARDING');
  const [selected, setSelected] = useState<RecruitmentSubmission | null>(null);
  const { data = [], isLoading, action } = useRecruitmentSubmissions(status);
  const currentTab = tabs.find((tab) => tab.status === status)!;
  const returnSubmission = (submission: RecruitmentSubmission) => {
    const reason = window.prompt('Co kandydat ma poprawić?');
    if (reason === null) return;
    action.mutate({ id: submission.id, action: 'return', reason });
  };

  return (
    <section>
      <div className="mb-4"><h2 className="text-xl font-bold text-gray-900">Wdrażanie wolontariuszy</h2><p className="text-sm text-gray-500">Decyzja od razu przenosi osobę do właściwego spisu.</p></div>
      <div className="mb-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
        {tabs.map((tab) => (
          <button key={tab.status} onClick={() => setStatus(tab.status)} className={`rounded-xl border px-4 py-3 text-sm font-bold transition-colors ${status === tab.status ? 'border-indigo-600 bg-indigo-600 text-white' : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'}`}>{tab.label}</button>
        ))}
      </div>
      <SubmissionList
        submissions={data}
        isLoading={isLoading}
        emptyText={currentTab.empty}
        onSelect={setSelected}
        actions={(submission) => status === 'ONBOARDING' ? (
          <>
            <button onClick={() => window.confirm(`Oznaczyć ${submission.full_name} jako wdrożoną osobę? Zostanie utworzony rekord wolontariusza.`) && action.mutate({ id: submission.id, action: 'accept' })} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white">Wdróż</button>
            <button onClick={() => window.confirm(`Odrzucić zgłoszenie ${submission.full_name}?`) && action.mutate({ id: submission.id, action: 'reject' })} className="rounded-lg bg-rose-600 px-3 py-2 text-xs font-bold text-white">Odrzuć</button>
            <button onClick={() => returnSubmission(submission)} className="rounded-lg bg-violet-50 px-3 py-2 text-xs font-bold text-violet-700">Zwróć formularz</button>
          </>
        ) : undefined}
      />
      {selected && <SubmissionDetailModal submission={selected} onClose={() => setSelected(null)} />}
    </section>
  );
};

export default RecruitmentOnboardingPage;
