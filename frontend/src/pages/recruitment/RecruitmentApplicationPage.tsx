import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useRecruitmentForm } from '@/hooks/useRecruitment';
import { parseApiError } from '@/lib/errors';
import { recruitmentService } from '@/services/recruitmentService';
import { recruitmentStatusLabel } from '@/features/recruitment/recruitmentStatus';
import type { RecruitmentField } from '@/types';

interface FieldControlProps {
  field: RecruitmentField;
  id: string;
  disabled?: boolean;
  value: unknown;
  onChange: (value: unknown) => void;
}

const controlClass =
  'mt-1 min-h-11 w-full rounded-lg border border-gray-200 bg-white px-3 text-gray-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100';

const FieldControl = ({ field, id, disabled, value, onChange }: FieldControlProps) => {
  if (field.field_type === 'textarea') {
    return <textarea id={id} rows={4} required={field.required} disabled={disabled} value={String(value ?? '')} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} className={`${controlClass} py-3`} />;
  }
  if (field.field_type === 'select') {
    return (
      <select id={id} required={field.required} disabled={disabled} value={String(value ?? '')} onChange={(event) => onChange(event.target.value)} className={controlClass}>
        <option value="">Wybierz odpowiedź</option>
        {field.options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    );
  }
  if (field.field_type === 'radio') {
    return (
      <div className="mt-2 space-y-2">
        {field.options.map((option) => (
          <label key={option} className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-gray-200 px-3 hover:bg-indigo-50">
            <input type="radio" name={field.key} value={option} required={field.required} checked={value === option} onChange={() => onChange(option)} className="h-4 w-4" />
            <span className="text-sm text-gray-700">{option}</span>
          </label>
        ))}
      </div>
    );
  }
  if (field.field_type === 'multiselect') {
    const selected = Array.isArray(value) ? value as string[] : [];
    return (
      <div className="mt-2 space-y-2">
        {field.options.map((option) => (
          <label key={option} className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-gray-200 px-3 hover:bg-indigo-50">
            <input
              type="checkbox"
              checked={selected.includes(option)}
              onChange={(event) => onChange(event.target.checked ? [...selected, option] : selected.filter((item) => item !== option))}
              className="h-4 w-4"
            />
            <span className="text-sm text-gray-700">{option}</span>
          </label>
        ))}
        {field.required && !selected.length && <p className="text-xs text-rose-600">Wybierz co najmniej jedną odpowiedź.</p>}
      </div>
    );
  }
  if (field.field_type === 'checkbox') {
    return (
      <label className="mt-2 flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-gray-200 px-3 hover:bg-indigo-50">
        <input id={id} type="checkbox" required={field.required} checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} className="h-4 w-4" />
        <span className="text-sm text-gray-700">Tak, potwierdzam</span>
      </label>
    );
  }
  return <input id={id} type={field.field_type} required={field.required} disabled={disabled} value={String(value ?? '')} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} className={controlClass} />;
};

interface RecruitmentApplicationPageProps {
  accessToken: string;
}

const RecruitmentApplicationPage = ({ accessToken }: RecruitmentApplicationPageProps) => {
  const { data: form, isLoading, isError, error } = useRecruitmentForm(accessToken);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const submit = useMutation({
    mutationFn: (answers: Record<string, unknown>) =>
      recruitmentService.submit(answers, accessToken),
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form) return;
    submit.mutate({
      ...form.initial_answers,
      ...answers,
      full_name: answers.full_name || form.applicant_name,
      email: form.applicant_email,
    });
  };

  if (submit.isSuccess || (form?.submission_status && form.submission_status !== 'RETURNED')) {
    const status = submit.data?.status ?? form?.submission_status;
    return (
      <main className="flex min-h-dvh items-center justify-center bg-[#1e2330] p-4">
        <section className="w-full max-w-xl rounded-2xl bg-white p-8 text-center shadow-2xl sm:p-12">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-3xl text-emerald-700">✓</div>
          <h1 className="mt-6 text-3xl font-bold text-gray-900">Dziękujemy za zgłoszenie</h1>
          <p className="mt-3 text-gray-600">Twoje odpowiedzi zostały zapisane. Skontaktujemy się z Tobą w sprawie kolejnego etapu.</p>
          {status && <p className="mt-5 rounded-lg bg-gray-100 p-3 text-sm font-bold text-gray-700">Aktualny status: {recruitmentStatusLabel[status]}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-dvh bg-[#1e2330] px-4 py-8 sm:py-12">
      <section className="mx-auto w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl">
        <header className="bg-gradient-to-br from-indigo-600 to-violet-700 p-6 text-white sm:p-9">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-100">A PAULO · Wolontariat</p>
          <h1 className="mt-3 text-3xl font-bold">{form?.title ?? 'Formularz rekrutacyjny'}</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-indigo-100">{form?.description ?? 'Opowiedz nam trochę o sobie.'}</p>
        </header>

        {isLoading ? (
          <div className="p-12 text-center text-gray-400">Ładowanie formularza…</div>
        ) : isError || !form ? (
          <div className="p-12 text-center text-rose-600">{parseApiError(error, 'Nie udało się załadować formularza.')}</div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6 p-6 sm:p-9">
            {form.return_reason && (
              <div className="rounded-lg border border-violet-200 bg-violet-50 p-4 text-sm text-violet-900">
                <strong>Formularz został zwrócony do poprawy:</strong> {form.return_reason}
              </div>
            )}
            <p className="text-sm text-gray-500"><span className="font-bold text-rose-600">*</span> Pola wymagane</p>
            {form.fields.map((field) => (
              <div key={field.id} className="text-sm font-bold text-gray-800">
                {field.field_type === 'radio' || field.field_type === 'multiselect' ? (
                  <span>{field.label} {field.required && <span className="text-rose-600">*</span>}</span>
                ) : (
                  <label htmlFor={`recruitment-${field.key}`}>{field.label} {field.required && <span className="text-rose-600">*</span>}</label>
                )}
                <FieldControl
                  field={field}
                  id={`recruitment-${field.key}`}
                  disabled={field.key === 'email'}
                  value={answers[field.key] ?? form.initial_answers[field.key] ?? (field.key === 'full_name' ? form.applicant_name : field.key === 'email' ? form.applicant_email : undefined)}
                  onChange={(value) => setAnswers((current) => ({ ...current, [field.key]: value }))}
                />
              </div>
            ))}
            {submit.isError && <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{parseApiError(submit.error, 'Nie udało się wysłać formularza.')}</div>}
            <div className="border-t pt-6">
              <button disabled={submit.isPending} className="min-h-12 w-full rounded-xl bg-emerald-600 px-6 font-bold text-white transition hover:bg-emerald-700 disabled:opacity-50">{submit.isPending ? 'Wysyłanie…' : 'Wyślij zgłoszenie'}</button>
            </div>
          </form>
        )}
      </section>
    </main>
  );
};

export default RecruitmentApplicationPage;
