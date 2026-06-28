import Modal from '@/components/ui/Modal';
import StatusBadge from '@/components/ui/StatusBadge';
import { formatRecruitmentDate, recruitmentStatusClass, recruitmentStatusLabel } from './recruitmentStatus';
import type { RecruitmentSubmission } from '@/types';

interface Props {
  submission: RecruitmentSubmission;
  onClose: () => void;
}

const formatValue = (value: unknown) => {
  if (typeof value === 'boolean') return value ? 'Tak' : 'Nie';
  if (Array.isArray(value)) return value.join(', ');
  return value === null || value === undefined || value === '' ? '—' : String(value);
};

const SubmissionDetailModal = ({ submission, onClose }: Props) => (
  <Modal onClose={onClose} maxWidth="max-w-3xl">
    <div className="flex flex-col gap-3 border-b pb-5 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-indigo-600">Pełne odpowiedzi</p>
        <h2 className="mt-1 text-2xl font-bold text-gray-900">{submission.full_name}</h2>
        <p className="mt-1 text-sm text-gray-500">Wysłano {formatRecruitmentDate(submission.submitted_at)}</p>
      </div>
      <StatusBadge status={recruitmentStatusLabel[submission.status]} colorClass={recruitmentStatusClass[submission.status]} />
    </div>

    {submission.return_reason && (
      <div className="mt-5 rounded-lg border border-violet-200 bg-violet-50 p-4">
        <p className="text-xs font-bold uppercase text-violet-700">Powód ostatniego zwrotu</p>
        <p className="mt-1 text-sm text-violet-900">{submission.return_reason}</p>
      </div>
    )}

    <dl className="mt-5 grid gap-3 sm:grid-cols-2">
      {submission.answers.map((answer) => (
        <div key={answer.key} className="rounded-lg border border-gray-200 bg-gray-50 p-4 sm:odd:col-span-1">
          <dt className="text-xs font-bold uppercase tracking-wide text-gray-400">{answer.label}</dt>
          <dd className="mt-2 whitespace-pre-wrap break-words text-sm font-medium text-gray-800">{formatValue(answer.value)}</dd>
        </div>
      ))}
    </dl>

    <div className="mt-6 flex justify-end border-t pt-4">
      <button onClick={onClose} className="rounded-lg bg-gray-900 px-5 py-2 font-bold text-white">Zamknij</button>
    </div>
  </Modal>
);

export default SubmissionDetailModal;
