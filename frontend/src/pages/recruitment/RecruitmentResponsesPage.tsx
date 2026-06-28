import { useMemo, useState } from 'react';
import SubmissionDetailModal from '@/features/recruitment/SubmissionDetailModal';
import SubmissionList from '@/features/recruitment/SubmissionList';
import { useRecruitmentSubmissions } from '@/hooks/useRecruitment';
import type { RecruitmentSubmission } from '@/types';

const RecruitmentResponsesPage = () => {
  const { data = [], isLoading, action } = useRecruitmentSubmissions();
  const [selected, setSelected] = useState<RecruitmentSubmission | null>(null);
  const [search, setSearch] = useState('');
  const returnSubmission = (submission: RecruitmentSubmission) => {
    const reason = window.prompt('Powód zwrotu formularza (opcjonalnie):');
    if (reason === null) return;
    action.mutate({ id: submission.id, action: 'return', reason });
  };
  const rows = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return data;
    return data.filter((item) => `${item.full_name} ${item.email} ${item.phone}`.toLowerCase().includes(query));
  }, [data, search]);

  return (
    <section>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div><h2 className="text-xl font-bold text-gray-900">Odpowiedzi z formularza</h2><p className="text-sm text-gray-500">Każdy rekord zawiera pełną migawkę pytań i odpowiedzi.</p></div>
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Szukaj osoby…" className="min-h-10 rounded-lg border border-gray-200 bg-gray-50 px-4 text-sm outline-none focus:border-indigo-500 sm:w-72" />
      </div>
      <SubmissionList
        submissions={rows}
        isLoading={isLoading}
        emptyText="Nikt jeszcze nie wypełnił formularza."
        onSelect={setSelected}
        actions={(submission) => submission.status === 'SUBMITTED' ? (
          <>
            <button onClick={() => action.mutate({ id: submission.id, action: 'start-onboarding' })} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white">Do wdrażania</button>
            <button onClick={() => returnSubmission(submission)} className="rounded-lg bg-violet-50 px-3 py-2 text-xs font-bold text-violet-700">Zwróć</button>
          </>
        ) : undefined}
      />
      {selected && <SubmissionDetailModal submission={selected} onClose={() => setSelected(null)} />}
    </section>
  );
};

export default RecruitmentResponsesPage;
