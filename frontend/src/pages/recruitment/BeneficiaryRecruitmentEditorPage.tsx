import SurveyFieldBuilder from '@/features/surveys/SurveyFieldBuilder';
import {
  useBeneficiaryRecruitmentAccessLink,
  useBeneficiaryRecruitmentFields,
} from '@/hooks/useBeneficiaryRecruitment';
import { useHasPermission } from '@/hooks/usePermissions';
import { appDialog } from '@/lib/appDialog';
import { parseApiError } from '@/lib/errors';

const BeneficiaryRecruitmentEditorPage = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_RECRUITMENT');
  const fields = useBeneficiaryRecruitmentFields();
  const link = useBeneficiaryRecruitmentAccessLink();
  const publicUrl = link.data ? `${window.location.origin}${link.data}` : '';

  return (
    <section className="space-y-6">
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
        <h2 className="font-bold text-emerald-950">Publiczny link do ankiety podopiecznych</h2>
        <p className="mt-1 text-sm text-emerald-800">Link nie wymaga logowania. Udostępniaj go tylko osobom i instytucjom zgłaszającym.</p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <input readOnly value={publicUrl} placeholder="Ładowanie linku…" className="min-h-10 flex-1 rounded-lg border border-emerald-200 bg-white px-3 text-sm" />
          <button type="button" disabled={!publicUrl} onClick={async () => { await navigator.clipboard.writeText(publicUrl); appDialog.success('Link został skopiowany.'); }} className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">Kopiuj link</button>
        </div>
      </div>
      <SurveyFieldBuilder
        title="Ankieta rekrutacji podopiecznych"
        description="Pytania widoczne w publicznym formularzu zgłoszeniowym."
        fields={fields.data ?? []}
        isLoading={fields.isLoading}
        isSaving={fields.save.isPending}
        canManage={canManage}
        onSave={(draft, onSuccess) => fields.save.mutate(draft, { onSuccess })}
        error={fields.isError ? <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{parseApiError(fields.error)}</p> : undefined}
        systemFieldHelp="To pole jest potrzebne do automatycznego utworzenia podopiecznego. Możesz zmienić jego etykietę i podpowiedź."
      />
    </section>
  );
};

export default BeneficiaryRecruitmentEditorPage;
