import { useMemo, useState } from 'react';
import SurveyFieldModal from '@/features/surveys/SurveyFieldModal';
import { useDepartureFields } from '@/hooks/useDepartures';
import { useHasPermission } from '@/hooks/usePermissions';
import { parseApiError } from '@/lib/errors';
import type { DepartureFieldDraft, RecruitmentFieldDraft } from '@/types';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';

const DepartureEditorPage = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_RECRUITMENT');
  const fieldsQuery = useDepartureFields();
  const [draft, setDraft] = useState<DepartureFieldDraft[] | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null | undefined>(undefined);
  const confirmDiscard = useUnsavedChanges(draft !== null && !fieldsQuery.save.isPending);
  const fields = draft ?? fieldsQuery.data ?? [];
  const editingField = useMemo(() => {
    if (editingIndex === undefined || editingIndex === null || !draft) return null;
    return draft[editingIndex] ?? null;
  }, [draft, editingIndex]);

  const startEditing = () => setDraft((fieldsQuery.data ?? []).map((field) => ({
    id: field.id,
    is_system: field.is_system,
    label: field.label,
    field_type: field.field_type,
    required: field.required,
    placeholder: field.placeholder,
    options: [...field.options],
    is_active: field.is_active,
  })));

  const applyField = (field: RecruitmentFieldDraft) => {
    if (field.field_type === 'email' || field.field_type === 'tel') return;
    const departureField = field as DepartureFieldDraft;
    setDraft((current) => {
      if (!current) return current;
      if (editingIndex === null) return [...current, departureField];
      return current.map((item, index) => index === editingIndex ? departureField : item);
    });
    setEditingIndex(undefined);
  };

  const move = (index: number, offset: -1 | 1) => setDraft((current) => {
    if (!current || !current[index + offset]) return current;
    const copy = [...current];
    [copy[index], copy[index + offset]] = [copy[index + offset]!, copy[index]!];
    return copy;
  });

  const remove = (index: number) => setDraft((current) => (
    current?.filter((field, fieldIndex) => field.is_system || fieldIndex !== index) ?? current
  ));

  const save = () => {
    if (!draft) return;
    fieldsQuery.save.mutate(draft, { onSuccess: () => setDraft(null) });
  };

  return (
    <section>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Pytania przy odejściu</h2>
          <p className="text-sm text-gray-500">Zmiany są wysyłane dopiero po kliknięciu „Zapisz”.</p>
        </div>
        {canManage && draft ? (
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => setEditingIndex(null)} className="rounded-lg bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-700">+ Dodaj pytanie</button>
            <button type="button" onClick={() => confirmDiscard() && setDraft(null)} className="rounded-lg border px-4 py-2 text-sm font-bold text-gray-600">Anuluj</button>
            <button type="button" onClick={save} disabled={fieldsQuery.save.isPending} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">Zapisz</button>
          </div>
        ) : canManage ? (
          <button type="button" onClick={startEditing} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white">Edytuj pytania</button>
        ) : null}
      </div>
      {fieldsQuery.save.isError && <p className="mb-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{parseApiError(fieldsQuery.save.error, 'Nie udało się zapisać pytań.')}</p>}
      <div className="space-y-2">
        {fields.map((field, index) => (
          <article key={field.id ?? `new-${index}`} className="flex flex-col gap-3 rounded-xl border bg-white p-4 sm:flex-row sm:items-center">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-sm font-bold text-gray-500">{index + 1}</span>
            <div className="min-w-0 flex-1">
              <p className="font-bold text-gray-900">{field.label}</p>
              <p className="text-xs text-gray-500">{field.field_type}{field.required ? ' · wymagane' : ''}{field.is_system ? ' · podstawowe' : ''}</p>
            </div>
            {draft && (
              <div className="flex gap-2">
                <button type="button" disabled={index === 0} onClick={() => move(index, -1)} className="rounded border px-2 py-1 disabled:opacity-30">↑</button>
                <button type="button" disabled={index === fields.length - 1} onClick={() => move(index, 1)} className="rounded border px-2 py-1 disabled:opacity-30">↓</button>
                <button type="button" onClick={() => setEditingIndex(index)} className="rounded bg-indigo-50 px-3 py-1 text-sm font-bold text-indigo-700">Edytuj</button>
                {!field.is_system && <button type="button" onClick={() => remove(index)} className="rounded bg-rose-50 px-3 py-1 text-sm font-bold text-rose-700">Usuń</button>}
              </div>
            )}
          </article>
        ))}
      </div>

      {canManage && editingIndex !== undefined && (
        <SurveyFieldModal
          field={editingField}
          onClose={() => setEditingIndex(undefined)}
          onSave={applyField}
          excludedTypes={['email', 'tel']}
          systemFieldHelp="To podstawowe pole ankiety odejścia. Możesz zmienić jego nazwę i podpowiedź, ale nie typ, wymagalność ani aktywność."
        />
      )}
    </section>
  );
};

export default DepartureEditorPage;
