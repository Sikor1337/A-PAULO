import { useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import { useDepartureFields, useMyDepartureSurvey } from '@/hooks/useDepartures';
import { parseApiError } from '@/lib/errors';
import { useAuthStore } from '@/stores/authStore';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import type { DepartureAnswer, DepartureField } from '@/types';

const inputClass = 'mt-1 min-h-11 w-full rounded-lg border border-gray-200 px-3 outline-none focus:border-indigo-500';

const today = () => {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
};

interface FieldControlProps {
  field: Pick<DepartureField | DepartureAnswer, 'key' | 'label' | 'field_type' | 'required' | 'placeholder' | 'options'>;
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
  const user = useAuthStore((state) => state.user);
  const isAdminPreview = user?.status === 'admin';
  const survey = useMyDepartureSurvey(!isAdminPreview);
  const fieldsPreview = useDepartureFields(isAdminPreview);
  const [draftAnswers, setDraftAnswers] = useState<Record<string, unknown> | null>(null);
  useUnsavedChanges(draftAnswers !== null && !survey.save.isPending);
  const interview = survey.data?.interview;
  const formFields = isAdminPreview
    ? fieldsPreview.data ?? []
    : interview?.answers ?? survey.data?.fields ?? [];
  const savedAnswers = interview
    ? Object.fromEntries(interview.answers.map((answer) => [answer.key, answer.value]))
    : { departure_date: today() };
  const answers = draftAnswers ?? savedAnswers;
  const isLoading = isAdminPreview ? fieldsPreview.isLoading : survey.isLoading;
  const isError = isAdminPreview ? fieldsPreview.isError : survey.isError;
  const error = isAdminPreview ? fieldsPreview.error : survey.error;
  const hasData = isAdminPreview ? Boolean(fieldsPreview.data) : Boolean(survey.data);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!interview && !window.confirm('Wysłać ankietę odejścia?')) return;
    survey.save.mutate(answers);
  };

  return (
    <PageShell cardClassName="mx-auto min-h-[calc(100dvh-88px)] max-w-3xl rounded-xl bg-white p-4 shadow-lg sm:p-8 lg:min-h-[calc(100dvh-48px)]">
      <header className="mb-8 border-b pb-5">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">
          {isAdminPreview ? 'Panel administratora' : 'Moje konto'}
        </p>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">Ankieta odejścia</h1>
        <p className="mt-2 text-sm text-gray-500">
          {isAdminPreview
            ? 'Podgląd formularza widocznego dla wolontariusza.'
            : 'Wypełnij ankietę przed zakończeniem wolontariatu.'}
        </p>
      </header>

      {isLoading ? (
        <p className="py-12 text-center text-gray-500">Ładowanie ankiety…</p>
      ) : isError ? (
        <p className="rounded-xl bg-rose-50 p-4 text-rose-700">
          {parseApiError(error, 'Nie udało się pobrać ankiety odejścia.')}
        </p>
      ) : hasData ? (
        <form onSubmit={submit} className="space-y-6">
          {isAdminPreview ? (
            <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-900">
              Tryb podglądu administratora. Odpowiedzi nie zostaną zapisane.
            </div>
          ) : survey.data ? (
            <div className="rounded-xl bg-indigo-50 p-4 text-sm text-indigo-900">
              Ankietę wypełnia: <strong>{survey.data.volunteer.full_name}</strong>
            </div>
          ) : null}
          {!isAdminPreview && interview && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
              Ankieta została wysłana. Możesz nadal poprawiać odpowiedzi.
            </div>
          )}
          <fieldset disabled={isAdminPreview} className="space-y-6 disabled:opacity-75">
            {formFields.map((field) => (
              <label key={field.key} className="block text-sm font-semibold text-gray-700">
                <span>
                  {field.label} {field.required && <span className="text-rose-600">*</span>}
                </span>
                <FieldControl
                  field={field}
                  value={answers[field.key]}
                  onChange={(value) => setDraftAnswers((current) => ({
                    ...(current ?? answers),
                    [field.key]: value,
                  }))}
                />
              </label>
            ))}
          </fieldset>
          {!isAdminPreview && survey.save.isError && (
            <p className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">
              {parseApiError(survey.save.error, 'Nie udało się zapisać ankiety odejścia.')}
            </p>
          )}
          {!isAdminPreview && (
            <div className="flex justify-end border-t pt-5">
              <button
                type="submit"
                disabled={survey.save.isPending}
                className="min-h-11 rounded-lg bg-indigo-600 px-6 py-2 font-bold text-white disabled:opacity-50"
              >
                {survey.save.isPending
                  ? 'Zapisywanie…'
                  : interview ? 'Zapisz zmiany' : 'Wyślij ankietę'}
              </button>
            </div>
          )}
        </form>
      ) : null}
    </PageShell>
  );
};

export default MyDepartureSurveyPage;
