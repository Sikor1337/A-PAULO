import StatusBadge from '@/components/ui/StatusBadge';
import { SurveyResponses } from '@/features/surveys';
import { formatRecruitmentDate, recruitmentStatusClass, recruitmentStatusLabel } from '@/features/recruitment/recruitmentStatus';
import { useRecruitmentSubmissions } from '@/hooks/useRecruitment';
import { useHasPermission } from '@/hooks/usePermissions';
import { appDialog } from '@/lib/appDialog';

const RecruitmentResponsesPage = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_RECRUITMENT');
  const { data = [], isLoading, action } = useRecruitmentSubmissions();
  const records = data.map((submission) => ({
    id: submission.id,
    title: submission.full_name,
    subtitle: `Wysłano ${formatRecruitmentDate(submission.submitted_at)}`,
    summary: `${submission.email} ${submission.phone}`,
    answers: submission.answers,
    source: submission,
    badge: <StatusBadge status={recruitmentStatusLabel[submission.status]} colorClass={recruitmentStatusClass[submission.status]} />,
    notices: [
      ...(submission.return_reason ? [{ label: 'Powód ostatniego zwrotu', value: submission.return_reason, className: 'border-violet-200 bg-violet-50 text-violet-900' }] : []),
      ...(submission.decision_comment ? [{ label: 'Komentarz do decyzji', value: submission.decision_comment, className: 'border-blue-200 bg-blue-50 text-blue-950' }] : []),
    ],
  }));

  return (
    <SurveyResponses
      title="Odpowiedzi rekrutacyjne"
      description="Pełne migawki pytań i odpowiedzi kandydatów."
      records={records}
      isLoading={isLoading}
      emptyText="Nikt jeszcze nie wypełnił formularza."
      actions={canManage ? (record) => record.source.status === 'SUBMITTED' ? <>
        <button type="button" onClick={() => action.mutate({ id: record.id, action: 'start-onboarding' })} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white">Do wdrażania</button>
        <button type="button" onClick={async () => {
          const reason = await appDialog.prompt('Powód zwrotu formularza (opcjonalnie):', { title: 'Zwróć formularz', confirmLabel: 'Zwróć' });
          if (reason !== null) action.mutate({ id: record.id, action: 'return', note: reason });
        }} className="rounded-lg bg-violet-50 px-3 py-2 text-xs font-bold text-violet-700">Zwróć</button>
      </> : undefined : undefined}
    />
  );
};

export default RecruitmentResponsesPage;
