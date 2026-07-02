import { useMemo, useState } from 'react';
import RecruitmentFieldModal from '@/features/recruitment/RecruitmentFieldModal';
import { useRecruitmentFields } from '@/hooks/useRecruitment';
import { useHasPermission } from '@/hooks/usePermissions';
import type { RecruitmentFieldDraft, RecruitmentFieldType } from '@/types';

const typeLabels: Record<RecruitmentFieldType, string> = {
  text: 'Krótka odpowiedź',
  textarea: 'Długa odpowiedź',
  email: 'E-mail',
  tel: 'Telefon',
  date: 'Data',
  select: 'Lista wyboru',
  radio: 'Jedna z opcji',
  multiselect: 'Wiele z wielu',
  checkbox: 'Potwierdzenie',
};

const RecruitmentFormBuilderPage = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_RECRUITMENT');
  const { data = [], isLoading, save } = useRecruitmentFields();
  const [draft, setDraft] = useState<RecruitmentFieldDraft[] | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null | undefined>(undefined);
  const [copied, setCopied] = useState(false);
  const applicationUrl = `${window.location.origin}/recruitment/apply`;
  const fields = draft ?? data;

  const editingField = useMemo(() => {
    if (editingIndex === undefined || editingIndex === null || !draft) return null;
    return draft[editingIndex] ?? null;
  }, [draft, editingIndex]);

  const beginEditing = () => {
    setDraft(data.map((field) => ({
      id: field.id,
      is_system: field.is_system,
      label: field.label,
      field_type: field.field_type,
      required: field.required,
      placeholder: field.placeholder,
      options: [...field.options],
      is_active: field.is_active,
    })));
  };

  const applyField = (field: RecruitmentFieldDraft) => {
    setDraft((current) => {
      if (!current) return current;
      if (editingIndex === null) return [...current, field];
      if (editingIndex === undefined) return current;
      return current.map((item, index) => index === editingIndex ? field : item);
    });
    setEditingIndex(undefined);
  };

  const move = (index: number, direction: -1 | 1) => {
    setDraft((current) => {
      if (!current || !current[index + direction]) return current;
      const ordered = [...current];
      [ordered[index], ordered[index + direction]] = [ordered[index + direction]!, ordered[index]!];
      return ordered;
    });
  };

  const toggleActive = (index: number) => {
    setDraft((current) => current?.map((field, itemIndex) => (
      itemIndex === index ? { ...field, is_active: !field.is_active } : field
    )) ?? current);
  };

  const remove = (index: number) => {
    if (!window.confirm('Usunąć to pole? Zapisane odpowiedzi pozostaną w archiwum.')) return;
    setDraft((current) => current?.filter((_, itemIndex) => itemIndex !== index) ?? current);
  };

  const saveDraft = () => {
    if (!draft) return;
    const payload = draft.map((field) => ({
      ...(field.id ? { id: field.id } : {}),
      label: field.label,
      field_type: field.field_type,
      required: field.required,
      placeholder: field.placeholder,
      options: field.options,
      is_active: field.is_active,
    }));
    save.mutate(payload, { onSuccess: () => setDraft(null) });
  };

  const copyLink = async () => {
    await navigator.clipboard.writeText(applicationUrl);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <section>
      <div className="mb-7 rounded-xl border border-indigo-100 bg-indigo-50 p-4 sm:p-5">
        <h2 className="font-bold text-indigo-950">Link do ankiety rekrutacyjnej</h2>
        <p className="mt-1 text-sm text-indigo-700">
          To jeden stały link dla wszystkich kandydatów. Po zalogowaniu każda osoba widzi własną ankietę.
        </p>
        <div className="mt-4 flex flex-col gap-2 rounded-lg bg-white p-3 sm:flex-row sm:items-center">
          <code className="min-w-0 flex-1 break-all text-xs text-indigo-900">{applicationUrl}</code>
          <button type="button" onClick={copyLink} className="shrink-0 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold text-white">
            {copied ? 'Skopiowano' : 'Kopiuj link'}
          </button>
        </div>
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Pytania w formularzu</h2>
          <p className="text-sm text-gray-500">
            {draft ? 'Zmiany są robocze. Kandydaci zobaczą je dopiero po zapisaniu.' : 'Uruchom edycję, wprowadź zmiany i zapisz je jednym żądaniem.'}
          </p>
        </div>
        {draft ? (
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => setEditingIndex(null)} className="rounded-lg bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-700">+ Dodaj pole</button>
            <button type="button" onClick={() => setDraft(null)} disabled={save.isPending} className="rounded-lg border px-4 py-2 text-sm font-bold text-gray-600">Anuluj</button>
            <button type="button" onClick={saveDraft} disabled={save.isPending} className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white disabled:opacity-50">
              {save.isPending ? 'Zapisywanie…' : 'Zapisz formularz'}
            </button>
          </div>
        ) : canManage ? (
          <button type="button" onClick={beginEditing} className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white">Edytuj formularz</button>
        ) : null}
      </div>

      {isLoading ? (
        <div className="p-10 text-center text-gray-400">Ładowanie…</div>
      ) : (
        <div className="space-y-3">
          {fields.map((field, index) => (
            <article key={field.id ?? `new-${index}`} className={`rounded-xl border p-4 ${field.is_active ? 'border-gray-200 bg-white' : 'border-dashed border-gray-300 bg-gray-50 opacity-70'}`}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                <div className="flex min-w-0 flex-1 gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-sm font-black text-gray-500">{index + 1}</span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-bold text-gray-900">{field.label}</h3>
                      {field.required && <span className="rounded bg-rose-100 px-2 py-0.5 text-[10px] font-bold uppercase text-rose-700">Wymagane</span>}
                      {field.is_system && <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-700">Podstawowe</span>}
                      {!field.is_active && <span className="rounded bg-gray-200 px-2 py-0.5 text-[10px] font-bold uppercase text-gray-600">Ukryte</span>}
                    </div>
                    <p className="mt-1 text-sm text-gray-500">{typeLabels[field.field_type]}{field.options.length ? ` · ${field.options.join(' / ')}` : ''}</p>
                  </div>
                </div>
                {draft && (
                  <div className="flex flex-wrap gap-2 sm:justify-end">
                    <button type="button" disabled={index === 0} onClick={() => move(index, -1)} className="rounded-lg border px-3 py-2 text-xs font-bold text-gray-500 disabled:opacity-30" aria-label="Przenieś wyżej">↑</button>
                    <button type="button" disabled={index === fields.length - 1} onClick={() => move(index, 1)} className="rounded-lg border px-3 py-2 text-xs font-bold text-gray-500 disabled:opacity-30" aria-label="Przenieś niżej">↓</button>
                    {!field.is_system && <button type="button" onClick={() => toggleActive(index)} className="rounded-lg border px-3 py-2 text-xs font-bold text-gray-600">{field.is_active ? 'Ukryj' : 'Pokaż'}</button>}
                    <button type="button" onClick={() => setEditingIndex(index)} className="rounded-lg bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-700">Edytuj</button>
                    {!field.is_system && <button type="button" onClick={() => remove(index)} className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">Usuń</button>}
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {canManage && editingIndex !== undefined && (
        <RecruitmentFieldModal
          field={editingField}
          onClose={() => setEditingIndex(undefined)}
          onSave={applyField}
        />
      )}
    </section>
  );
};

export default RecruitmentFormBuilderPage;
