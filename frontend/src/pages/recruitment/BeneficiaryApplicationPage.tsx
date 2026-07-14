import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import PublicSurveyField from '@/features/surveys/PublicSurveyField';
import { usePublicBeneficiaryRecruitmentForm } from '@/hooks/useBeneficiaryRecruitment';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import { parseApiError } from '@/lib/errors';
import { beneficiaryRecruitmentService } from '@/services/beneficiaryRecruitmentService';

const BeneficiaryApplicationPage = () => {
  const { token: accessToken = '' } = useParams();
  const formQuery = usePublicBeneficiaryRecruitmentForm(accessToken);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [website, setWebsite] = useState('');
  const submit = useMutation({
    mutationFn: () => beneficiaryRecruitmentService.submit(accessToken, formQuery.data!.form_token, answers, website),
  });
  useUnsavedChanges(Object.keys(answers).length > 0 && !submit.isSuccess && !submit.isPending);

  if (submit.isSuccess) return (
    <main className="flex min-h-dvh items-center justify-center bg-[#1e2330] p-4">
      <section className="w-full max-w-xl rounded-2xl bg-white p-10 text-center shadow-2xl">
        <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-emerald-100 text-3xl text-emerald-700">✓</div>
        <h1 className="mt-6 text-3xl font-bold text-gray-900">Dziękujemy za zgłoszenie</h1>
        <p className="mt-3 text-gray-600">Zespół A PAULO zapozna się z opisem i skontaktuje z osobą zgłaszającą.</p>
      </section>
    </main>
  );

  return (
    <main className="min-h-dvh bg-[#1e2330] px-4 py-8 sm:py-12">
      <section className="mx-auto max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl">
        <header className="bg-gradient-to-br from-emerald-600 to-teal-700 p-6 text-white sm:p-9">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-100">A PAULO · Pomoc</p>
          <h1 className="mt-3 text-3xl font-bold">{formQuery.data?.title ?? 'Zgłoszenie osoby potrzebującej pomocy'}</h1>
          <p className="mt-2 text-sm leading-6 text-emerald-50">{formQuery.data?.description}</p>
        </header>
        {formQuery.isLoading ? <p className="p-12 text-center text-gray-500">Ładowanie formularza…</p> : formQuery.isError || !formQuery.data ? (
          <p className="p-12 text-center text-rose-700">{parseApiError(formQuery.error, 'Nie udało się otworzyć formularza.')}</p>
        ) : (
          <form onSubmit={(event) => { event.preventDefault(); submit.mutate(); }} className="relative space-y-6 p-6 sm:p-9">
            <input value={website} onChange={(event) => setWebsite(event.target.value)} name="website" tabIndex={-1} autoComplete="off" className="absolute -left-[10000px] size-px" aria-hidden="true" />
            <p className="text-sm text-gray-500"><span className="font-bold text-rose-600">*</span> Pola wymagane</p>
            {formQuery.data.fields.map((field) => <div key={field.id} className="text-sm font-bold text-gray-800"><label htmlFor={`public-survey-${field.key}`}>{field.label} {field.required && <span className="text-rose-600">*</span>}</label><PublicSurveyField field={field} value={answers[field.key]} onChange={(value) => setAnswers((current) => ({ ...current, [field.key]: value }))} /></div>)}
            {submit.isError && <p className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">{parseApiError(submit.error, 'Nie udało się wysłać zgłoszenia.')}</p>}
            <button disabled={submit.isPending} className="min-h-12 w-full rounded-xl bg-emerald-600 px-6 font-bold text-white hover:bg-emerald-700 disabled:opacity-50">{submit.isPending ? 'Wysyłanie…' : 'Wyślij zgłoszenie'}</button>
          </form>
        )}
      </section>
    </main>
  );
};

export default BeneficiaryApplicationPage;
