import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import { useCreateDepartureInterview, useDepartureFields } from '@/hooks/useDepartures';
import { parseApiError } from '@/lib/errors';
import type { DepartureField, Volunteer } from '@/types';

interface Props {
  volunteer: Volunteer;
  onClose: () => void;
}

const inputClass = 'mt-1 min-h-11 w-full rounded-lg border border-gray-200 px-3 outline-none focus:border-indigo-500';
const today = () => {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
};

const FieldControl = ({
  field,
  value,
  onChange,
}: {
  field: DepartureField;
  value: unknown;
  onChange: (value: unknown) => void;
}) => {
  if (field.field_type === 'textarea') {
    return <textarea rows={4} required={field.required} value={String(value ?? '')} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} className={`${inputClass} py-3`} />;
  }
  if (field.field_type === 'checkbox') {
    return (
      <label className="mt-2 flex min-h-11 items-center gap-3 rounded-lg border px-3 font-normal">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
        Tak
      </label>
    );
  }
  if (field.field_type === 'select' || field.field_type === 'radio') {
    return (
      <select required={field.required} value={String(value ?? '')} onChange={(event) => onChange(event.target.value)} className={inputClass}>
        <option value="">Wybierz odpowiedź</option>
        {field.options.map((option) => <option key={option}>{option}</option>)}
      </select>
    );
  }
  if (field.field_type === 'multiselect') {
    const selected = Array.isArray(value) ? value as string[] : [];
    return (
      <div className="mt-2 space-y-2">
        {field.options.map((option) => (
          <label key={option} className="flex items-center gap-3 rounded-lg border px-3 py-2 font-normal">
            <input type="checkbox" checked={selected.includes(option)} onChange={(event) => onChange(event.target.checked ? [...selected, option] : selected.filter((item) => item !== option))} />
            {option}
          </label>
        ))}
      </div>
    );
  }
  return <input type={field.field_type} required={field.required} value={String(value ?? '')} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} className={inputClass} />;
};

const DepartureInterviewModal = ({ volunteer, onClose }: Props) => {
  const fields = useDepartureFields();
  const [answers, setAnswers] = useState<Record<string, unknown>>({
    departure_date: today(),
  });
  const create = useCreateDepartureInterview(onClose);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    create.mutate({ volunteerId: volunteer.id, answers });
  };

  return (
    <Modal onClose={onClose} maxWidth="max-w-2xl">
      <form onSubmit={submit} className="space-y-5">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-amber-600">Ankieta odejścia</p>
          <h2 className="mt-1 text-2xl font-bold text-gray-900">{volunteer.full_name}</h2>
          <p className="mt-1 text-sm text-gray-500">Zapisanie ankiety zmieni status wolontariusza na „Były”.</p>
        </div>
        {fields.isLoading ? (
          <p className="py-8 text-center text-gray-400">Ładowanie pytań…</p>
        ) : fields.isError ? (
          <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{parseApiError(fields.error, 'Nie udało się pobrać pytań ankiety.')}</p>
        ) : fields.data?.map((field) => (
          <div key={field.id} className="block text-sm font-semibold text-gray-700">
            <span>{field.label} {field.required && <span className="text-rose-600">*</span>}</span>
            <FieldControl field={field} value={answers[field.key]} onChange={(value) => setAnswers((current) => ({ ...current, [field.key]: value }))} />
          </div>
        ))}
        {create.isError && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{parseApiError(create.error, 'Nie udało się zapisać ankiety odejścia.')}</p>}
        <div className="flex justify-end gap-3 border-t pt-4">
          <button type="button" onClick={onClose} className="px-4 py-2 font-bold text-gray-500">Anuluj</button>
          <button disabled={create.isPending || fields.isLoading || fields.isError} className="rounded-lg bg-amber-600 px-5 py-2 font-bold text-white disabled:opacity-50">
            {create.isPending ? 'Zapisywanie…' : 'Zapisz odejście'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default DepartureInterviewModal;
