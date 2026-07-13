import SurveyFieldBuilder from '@/features/surveys/SurveyFieldBuilder';
import { useDepartureFields } from '@/hooks/useDepartures';
import { useHasPermission } from '@/hooks/usePermissions';
import { appDialog } from '@/lib/appDialog';
import { parseApiError } from '@/lib/errors';
import type { DepartureFieldDraft, RecruitmentFieldDraft } from '@/types';

const isDepartureField = (
  field: RecruitmentFieldDraft,
): field is DepartureFieldDraft => (
  field.field_type !== 'email' && field.field_type !== 'tel'
);

const DepartureEditorPage = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_RECRUITMENT');
  const fields = useDepartureFields();

  const saveFields = (
    draft: RecruitmentFieldDraft[],
    onSuccess: () => void,
  ) => {
    if (!draft.every(isDepartureField)) {
      appDialog.error('Ankieta odejścia nie obsługuje pól e-mail ani telefonu.');
      return;
    }
    fields.save.mutate(draft, { onSuccess });
  };

  const error = fields.isError || fields.save.isError
    ? (
      <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
        {parseApiError(
          fields.save.error ?? fields.error,
          'Nie udało się zapisać pytań.',
        )}
      </p>
    )
    : undefined;

  return (
    <SurveyFieldBuilder
      title="Pytania przy odejściu"
      description="Pytania widoczne w ankiecie odejścia wolontariusza."
      fields={fields.data ?? []}
      isLoading={fields.isLoading}
      isSaving={fields.save.isPending}
      canManage={canManage}
      onSave={saveFields}
      error={error}
      excludedTypes={['email', 'tel']}
      systemFieldHelp="To podstawowe pole ankiety odejścia. Możesz zmienić jego nazwę i podpowiedź, ale nie typ, wymagalność ani aktywność."
    />
  );
};

export default DepartureEditorPage;
