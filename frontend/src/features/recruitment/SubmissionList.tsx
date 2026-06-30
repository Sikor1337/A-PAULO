import StatusBadge from '@/components/ui/StatusBadge';
import { formatRecruitmentDate, recruitmentStatusClass, recruitmentStatusLabel } from './recruitmentStatus';
import type { ReactNode } from 'react';
import type { RecruitmentSubmission } from '@/types';

interface Props {
  submissions: RecruitmentSubmission[];
  isLoading: boolean;
  emptyText: string;
  onSelect: (submission: RecruitmentSubmission) => void;
  actions?: (submission: RecruitmentSubmission) => ReactNode;
}

const SubmissionList = ({ submissions, isLoading, emptyText, onSelect, actions }: Props) => {
  if (isLoading) return <div className="rounded-xl border border-gray-200 p-10 text-center text-gray-400">Ładowanie…</div>;
  if (!submissions.length) return <div className="rounded-xl border border-dashed border-gray-300 p-10 text-center text-gray-500">{emptyText}</div>;

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200">
      <div className="hidden grid-cols-[1.4fr_1.5fr_1fr_1fr_auto] gap-4 bg-[#1e2330] px-4 py-3 text-xs font-bold uppercase text-white md:grid">
        <span>Kandydat</span><span>Kontakt</span><span>Data</span><span>Status</span><span>Akcje</span>
      </div>
      <div className="divide-y divide-gray-100">
        {submissions.map((submission) => (
          <article key={submission.id} className="grid gap-3 p-4 transition-colors hover:bg-blue-50 md:grid-cols-[1.4fr_1.5fr_1fr_1fr_auto] md:items-center md:gap-4">
            <button onClick={() => onSelect(submission)} className="text-left font-bold text-gray-900 hover:text-indigo-600">{submission.full_name}</button>
            <div className="min-w-0 text-sm text-gray-600">
              <p className="truncate">{submission.email}</p><p>{submission.phone}</p>
            </div>
            <p className="text-sm text-gray-500">{formatRecruitmentDate(submission.submitted_at)}</p>
            <div><StatusBadge status={recruitmentStatusLabel[submission.status]} colorClass={recruitmentStatusClass[submission.status]} /></div>
            <div className="flex flex-wrap gap-2 md:justify-end">
              <button onClick={() => onSelect(submission)} className="rounded-lg border border-gray-200 px-3 py-2 text-xs font-bold text-gray-600 hover:bg-white">Odpowiedzi</button>
              {actions?.(submission)}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
};

export default SubmissionList;
