import { useState } from 'react';
import StatusBadge from '@/components/ui/StatusBadge';
import { SurveyResponses } from '@/features/surveys';
import { useBeneficiaryRecruitmentSubmissions } from '@/hooks/useBeneficiaryRecruitment';
import { useHasPermission } from '@/hooks/usePermissions';
import { appDialog } from '@/lib/appDialog';
import type { BeneficiaryRecruitmentStatus } from '@/types';

const statusMeta: Record<BeneficiaryRecruitmentStatus, { label: string; style: string }> = {
  NEW: { label: 'Nowe', style: 'bg-blue-100 text-blue-700' },
  BENEFICIARY_CREATED: { label: 'Utworzono podopiecznego', style: 'bg-emerald-100 text-emerald-700' },
  REJECTED: { label: 'Odrzucone', style: 'bg-rose-100 text-rose-700' },
  ARCHIVED: { label: 'Archiwalne', style: 'bg-gray-200 text-gray-700' },
};

const BeneficiaryRecruitmentResponsesPage = () => {
  const [includeArchived, setIncludeArchived] = useState(false);
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_RECRUITMENT');
  const query = useBeneficiaryRecruitmentSubmissions(includeArchived);
  const records = (query.data ?? []).map((submission) => ({
    id: submission.id,
    title: submission.full_name,
    subtitle: `Zgłoszono ${new Date(submission.submitted_at).toLocaleString('pl-PL')}`,
    summary: `${submission.address} · zgłasza ${submission.reporter_name}, ${submission.reporter_phone}`,
    answers: submission.answers,
    source: submission,
    badge: <StatusBadge status={statusMeta[submission.status].label} colorClass={statusMeta[submission.status].style} />,
    notices: submission.decision_comment ? [{ label: 'Komentarz do decyzji', value: submission.decision_comment }] : undefined,
  }));

  return (
    <section>
      <label className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-600"><input type="checkbox" checked={includeArchived} onChange={(event) => setIncludeArchived(event.target.checked)} /> Pokaż archiwalne</label>
      <SurveyResponses
        title="Zgłoszenia podopiecznych"
        description="Publiczne ankiety oczekujące na rozpatrzenie oraz historia decyzji."
        records={records}
        isLoading={query.isLoading}
        emptyText="Brak zgłoszeń."
        actions={canManage ? (record) => {
          const submission = record.source;
          if (submission.status === 'NEW') return <>
            <button type="button" onClick={async () => { if (await appDialog.confirm(`Utworzyć podopiecznego z danych ${submission.full_name}?`, { title: 'Utwórz podopiecznego', confirmLabel: 'Utwórz' })) query.createBeneficiary.mutate(submission.id); }} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white">Utwórz podopiecznego</button>
            <button type="button" onClick={async () => { const comment = await appDialog.prompt('Powód odrzucenia (opcjonalnie):', { title: 'Odrzuć zgłoszenie', confirmLabel: 'Odrzuć', tone: 'warning' }); if (comment !== null) query.reject.mutate({ id: submission.id, comment }); }} className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">Odrzuć</button>
          </>;
          return <>
            {submission.status !== 'ARCHIVED' && <button type="button" onClick={() => query.archive.mutate(submission.id)} className="rounded-lg bg-amber-50 px-3 py-2 text-xs font-bold text-amber-700">Archiwizuj</button>}
            <button type="button" onClick={async () => { if (await appDialog.confirm('Trwale usunąć ankietę? Utworzony podopieczny nie zostanie usunięty.', { title: 'Usuń ankietę', confirmLabel: 'Usuń', tone: 'error' })) query.remove.mutate(submission.id); }} className="rounded-lg bg-rose-600 px-3 py-2 text-xs font-bold text-white">Usuń</button>
          </>;
        } : undefined}
      />
    </section>
  );
};

export default BeneficiaryRecruitmentResponsesPage;
