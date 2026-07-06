import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import Modal from '@/components/ui/Modal';

export interface SurveyAnswerView {
  key: string;
  label: string;
  value: unknown;
}

export interface SurveyResponseRecord<T> {
  id: number;
  title: string;
  subtitle: string;
  summary?: string;
  answers: SurveyAnswerView[];
  source: T;
  badge?: ReactNode;
  notices?: Array<{ label: string; value: string; className?: string }>;
}

interface Props<T> {
  title: string;
  description: string;
  records: SurveyResponseRecord<T>[];
  isLoading: boolean;
  emptyText: string;
  actions?: (record: SurveyResponseRecord<T>) => ReactNode;
}

const displaySurveyAnswer = (value: unknown) => {
  if (typeof value === 'boolean') return value ? 'Tak' : 'Nie';
  if (Array.isArray(value)) return value.join(', ');
  return value === null || value === undefined || value === '' ? '—' : String(value);
};

const SurveyResponseModal = <T,>({ record, onClose }: { record: SurveyResponseRecord<T>; onClose: () => void }) => (
  <Modal onClose={onClose} maxWidth="max-w-3xl">
    <header className="flex flex-col gap-3 border-b pb-5 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-indigo-600">Pełne odpowiedzi</p>
        <h2 className="mt-1 text-2xl font-bold text-gray-900">{record.title}</h2>
        <p className="mt-1 text-sm text-gray-500">{record.subtitle}</p>
      </div>
      {record.badge}
    </header>
    {record.notices?.map((notice) => (
      <div key={notice.label} className={`mt-5 rounded-lg border p-4 ${notice.className ?? 'border-indigo-200 bg-indigo-50'}`}>
        <p className="text-xs font-bold uppercase">{notice.label}</p>
        <p className="mt-1 whitespace-pre-wrap text-sm">{notice.value}</p>
      </div>
    ))}
    <dl className="mt-5 grid gap-3 sm:grid-cols-2">
      {record.answers.map((answer) => (
        <div key={answer.key} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
          <dt className="text-xs font-bold uppercase tracking-wide text-gray-400">{answer.label}</dt>
          <dd className="mt-2 whitespace-pre-wrap break-words text-sm font-medium text-gray-800">{displaySurveyAnswer(answer.value)}</dd>
        </div>
      ))}
    </dl>
    <div className="mt-6 flex justify-end border-t pt-4">
      <button type="button" onClick={onClose} className="rounded-lg bg-gray-900 px-5 py-2 font-bold text-white">Zamknij</button>
    </div>
  </Modal>
);

const SurveyResponses = <T,>({ title, description, records, isLoading, emptyText, actions }: Props<T>) => {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<SurveyResponseRecord<T> | null>(null);
  const visible = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return records;
    return records.filter((record) => `${record.title} ${record.subtitle} ${record.summary ?? ''}`.toLowerCase().includes(query));
  }, [records, search]);

  return (
    <section>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div><h2 className="text-xl font-bold text-gray-900">{title}</h2><p className="text-sm text-gray-500">{description}</p></div>
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Szukaj osoby…" className="min-h-10 rounded-lg border border-gray-200 bg-gray-50 px-4 text-sm outline-none focus:border-indigo-500 sm:w-72" />
      </div>
      {isLoading ? <p className="p-10 text-center text-gray-400">Ładowanie…</p> : visible.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center text-gray-500">{emptyText}</div>
      ) : (
        <div className="space-y-3">
          {visible.map((record) => (
            <article key={record.id} className="flex flex-col gap-3 rounded-xl border bg-white p-4 transition hover:border-indigo-300 sm:flex-row sm:items-center">
              <button type="button" onClick={() => setSelected(record)} className="min-w-0 flex-1 text-left">
                <div className="flex flex-wrap items-center gap-2"><h3 className="font-bold text-gray-900">{record.title}</h3>{record.badge}</div>
                <p className="mt-1 text-sm text-gray-500">{record.subtitle}</p>
                {record.summary && <p className="mt-1 truncate text-sm text-gray-700">{record.summary}</p>}
              </button>
              {actions && <div className="flex flex-wrap gap-2">{actions(record)}</div>}
            </article>
          ))}
        </div>
      )}
      {selected && <SurveyResponseModal record={selected} onClose={() => setSelected(null)} />}
    </section>
  );
};

export default SurveyResponses;
