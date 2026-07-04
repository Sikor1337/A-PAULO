import { useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import { useMyDepartureSurvey } from '@/hooks/useDepartures';
import { parseApiError } from '@/lib/errors';
import type { DepartureField } from '@/types';

const inputClass = 'mt-1 min-h-11 w-full rounded-lg border border-gray-200 px-3 outline-none focus:border-indigo-500';

const today = () => {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
};

interface FieldControlProps {
  field: DepartureField;
  value: unknown;
  onChange: (value: unknown) => void;
}

const FieldControl = ({ field, value, onChange }: FieldControlProps) => {
  if (field.field_type === 'textarea') {
    return (
      <textarea
        rows={4}
        required={field.required}
        value={String(value ?? '')}
        placeholder={field.placeholder}
        onChange={(event) => onChange(event.target.value)}
        className={`${inputClass} py-3`}
      />
    );
  }
  if (field.field_type === 'checkbox') {
    return (
      <label className="mt-2 flex min-h-11 items-center gap-3 rounded-lg border px-3 font-normal">
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(event) => onChange(event.target.checked)}
        />
        Tak
      </label>
    );
  }
  if (field.field_type === 'select' || field.field_type === 'radio') {
    return (
      <select
        required={field.required}
        value={String(value ?? '')}
        onChange={(event) => onChange(event.target.value)}
        className={inputClass}
      >
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
            <input
              type="checkbox"
              checked={selected.includes(option)}
              onChange={(event) => onChange(
                event.target.checked
                  ? [...selected, option]
                  : selected.filter((item) => item !== option),
              )}
            />
            {option}
          </label>
        ))}
      </div>
    );
  }
  return (
    <input
      type={field.field_type}
      required={field.required}
      value={String(value ?? '')}
      placeholder={field.placeholder}
      onChange={(event) => onChange(event.target.value)}
      className={inputClass}
    />
  );
};

const MyDepartureSurveyPage = () => {
  const survey = useMyDepartureSurvey();
  const [answers, setAnswers] = useState<Record<string, unknown>>({
    departure_date: today(),
  });

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!window.confirm('Wysłać ankietę? Po wysłaniu nie będzie można jej edytować.')) return;
    survey.submit.mutate(answers);
  };

  return (
    <PageShell cardClassName="mx-auto min-h-[calc(100dvh-88px)] max-w-3xl rounded-xl bg-white p-4 shadow-lg sm:p-8 lg:min-h-[calc(100dvh-48px)]">
      <header className="mb-8 border-b pb-5">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">Moje konto</p>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">Ankieta odejścia</h1>
        <p className="mt-2 text-sm text-gray-500">Wypełnij ankietę przed zakończeniem wolontariatu.</p>
      </header>

      {survey.isLoading ? (
        <p className="py-12 text-center text-gray-500">Ładowanie ankiety…</p>
      ) : survey.isError ? (
        <p className="rounded-xl bg-rose-50 p-4 text-rose-700">
          {parseApiError(survey.error, 'Nie udało się pobrać ankiety odejścia.')}
        </p>
      ) : survey.data?.interview ? (
        <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-6">
          <h2 className="text-lg font-bold text-emerald-900">Ankieta została wysłana</h2>
          <p className="mt-2 text-sm text-emerald-800">
            Dziękujemy za jej wypełnienie. Data odejścia: {survey.data.interview.departure_date}.
          </p>
        </section>
      ) : survey.data ? (
        <form onSubmit={submit} className="space-y-6">
          <div className="rounded-xl bg-indigo-50 p-4 text-sm text-indigo-900">
            Ankietę wypełnia: <strong>{survey.data.volunteer.full_name}</strong>
          </div>
          {survey.data.fields.map((field) => (
            <label key={field.id} className="block text-sm font-semibold text-gray-700">
              <span>
                {field.label} {field.required && <span className="text-rose-600">*</span>}
              </span>
              <FieldControl
                field={field}
                value={answers[field.key]}
                onChange={(value) => setAnswers((current) => ({ ...current, [field.key]: value }))}
              />
            </label>
          ))}
          {survey.submit.isError && (
            <p className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">
              {parseApiError(survey.submit.error, 'Nie udało się wysłać ankiety odejścia.')}
            </p>
          )}
          <div className="flex justify-end border-t pt-5">
            <button
              type="submit"
              disabled={survey.submit.isPending}
              className="min-h-11 rounded-lg bg-indigo-600 px-6 py-2 font-bold text-white disabled:opacity-50"
            >
              {survey.submit.isPending ? 'Wysyłanie…' : 'Wyślij ankietę'}
            </button>
          </div>
        </form>
      ) : null}
    </PageShell>
  );
};

export default MyDepartureSurveyPage;
