import { useMemo, useState } from 'react';
import SurveyFieldModal from './SurveyFieldModal';
import { appDialog } from '@/lib/appDialog';
import type { RecruitmentFieldDraft, RecruitmentFieldType } from '@/types';

const typeLabels: Record<RecruitmentFieldType, string> = {
  text: 'Krótka odpowiedź', textarea: 'Długa odpowiedź', email: 'E-mail', tel: 'Telefon',
  date: 'Data', select: 'Lista wyboru', radio: 'Jedna z opcji', multiselect: 'Wiele z wielu', checkbox: 'Potwierdzenie',
};

interface Props {
  title: string;
  description: string;
  fields: RecruitmentFieldDraft[];
  isLoading: boolean;
  isSaving: boolean;
  canManage: boolean;
  onSave: (fields: RecruitmentFieldDraft[], onSuccess: () => void) => void;
  error?: React.ReactNode;
  excludedTypes?: RecruitmentFieldType[];
  systemFieldHelp?: string;
}

const cloneFields = (fields: RecruitmentFieldDraft[]) => fields.map((field) => ({
  ...field,
  options: [...field.options],
}));

const SurveyFieldBuilder = ({
  title, description, fields: savedFields, isLoading, isSaving, canManage,
  onSave, error, excludedTypes, systemFieldHelp,
}: Props) => {
  const [draft, setDraft] = useState<RecruitmentFieldDraft[] | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null | undefined>(undefined);
  const fields = draft ?? savedFields;
  const editingField = useMemo(() => (
    editingIndex === undefined || editingIndex === null || !draft
      ? null
      : draft[editingIndex] ?? null
  ), [draft, editingIndex]);

  const applyField = (field: RecruitmentFieldDraft) => {
    setDraft((current) => {
      if (!current || editingIndex === undefined) return current;
      if (editingIndex === null) return [...current, field];
      return current.map((item, index) => index === editingIndex ? field : item);
    });
    setEditingIndex(undefined);
  };
  const move = (index: number, offset: -1 | 1) => setDraft((current) => {
    if (!current || !current[index + offset]) return current;
    const copy = [...current];
    [copy[index], copy[index + offset]] = [copy[index + offset]!, copy[index]!];
    return copy;
  });
  const remove = async (index: number) => {
    if (!await appDialog.confirm('Usunąć to pole? Zapisane odpowiedzi pozostaną w archiwum.', { title: 'Usuwanie pola ankiety', confirmLabel: 'Usuń', tone: 'warning' })) return;
    setDraft((current) => current?.filter((_, fieldIndex) => fieldIndex !== index) ?? current);
  };

  return (
    <section>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
          <p className="text-sm text-gray-500">{draft ? 'Zmiany są robocze i będą widoczne dopiero po zapisaniu.' : description}</p>
        </div>
        {draft ? (
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => setEditingIndex(null)} className="rounded-lg bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-700">+ Dodaj pytanie</button>
            <button type="button" onClick={() => setDraft(null)} disabled={isSaving} className="rounded-lg border px-4 py-2 text-sm font-bold text-gray-600">Anuluj</button>
            <button type="button" onClick={() => onSave(draft, () => setDraft(null))} disabled={isSaving} className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white disabled:opacity-50">{isSaving ? 'Zapisywanie…' : 'Zapisz formularz'}</button>
          </div>
        ) : canManage ? (
          <button type="button" onClick={() => setDraft(cloneFields(savedFields))} className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white">Edytuj formularz</button>
        ) : null}
      </div>
      {error}
      {isLoading ? <div className="p-10 text-center text-gray-400">Ładowanie…</div> : (
        <div className="space-y-3">
          {fields.map((field, index) => (
            <article key={field.id ?? `new-${index}`} className={`rounded-xl border p-4 ${field.is_active ? 'border-gray-200 bg-white' : 'border-dashed border-gray-300 bg-gray-50 opacity-70'}`}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-sm font-black text-gray-500">{index + 1}</span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-bold text-gray-900">{field.label}</h3>
                    {field.required && <span className="rounded bg-rose-100 px-2 py-0.5 text-[10px] font-bold uppercase text-rose-700">Wymagane</span>}
                    {field.is_system && <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-700">Podstawowe</span>}
                    {!field.is_active && <span className="rounded bg-gray-200 px-2 py-0.5 text-[10px] font-bold uppercase text-gray-600">Ukryte</span>}
                  </div>
                  <p className="mt-1 text-sm text-gray-500">{typeLabels[field.field_type]}{field.options.length ? ` · ${field.options.join(' / ')}` : ''}</p>
                </div>
                {draft && <div className="flex flex-wrap gap-2">
                  <button type="button" disabled={index === 0} onClick={() => move(index, -1)} className="rounded-lg border px-3 py-2 text-xs font-bold disabled:opacity-30">↑</button>
                  <button type="button" disabled={index === fields.length - 1} onClick={() => move(index, 1)} className="rounded-lg border px-3 py-2 text-xs font-bold disabled:opacity-30">↓</button>
                  {!field.is_system && <button type="button" onClick={() => setDraft((current) => current?.map((item, itemIndex) => itemIndex === index ? { ...item, is_active: !item.is_active } : item) ?? current)} className="rounded-lg border px-3 py-2 text-xs font-bold">{field.is_active ? 'Ukryj' : 'Pokaż'}</button>}
                  <button type="button" onClick={() => setEditingIndex(index)} className="rounded-lg bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-700">Edytuj</button>
                  {!field.is_system && <button type="button" onClick={() => remove(index)} className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">Usuń</button>}
                </div>}
              </div>
            </article>
          ))}
        </div>
      )}
      {canManage && editingIndex !== undefined && <SurveyFieldModal field={editingField} onClose={() => setEditingIndex(undefined)} onSave={applyField} excludedTypes={excludedTypes} systemFieldHelp={systemFieldHelp} />}
    </section>
  );
};

export default SurveyFieldBuilder;
