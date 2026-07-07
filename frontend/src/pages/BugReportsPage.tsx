import { useRef, useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import { useBugReportActions, useBugReportList, useMyBugReports } from '@/hooks/useBugReports';
import { useHasPermission } from '@/hooks/usePermissions';
import { formatDate } from '@/lib/date';
import { bugReportService, BUG_REPORT_ACCEPT } from '@/services/bugReportService';
import type { BugReport, BugReportStatus } from '@/types';

const STATUS_OPTIONS: BugReportStatus[] = ['NOWY', 'W_TRAKCIE', 'ROZWIĄZANY', 'ODRZUCONY'];

const STATUS_STYLES: Record<BugReportStatus, string> = {
  NOWY: 'bg-blue-100 text-blue-700',
  W_TRAKCIE: 'bg-amber-100 text-amber-700',
  ROZWIĄZANY: 'bg-emerald-100 text-emerald-700',
  ODRZUCONY: 'bg-rose-100 text-rose-700',
};

const StatusBadge = ({ status }: { status: BugReportStatus }) => (
  <span className={`rounded px-2 py-0.5 text-[11px] font-bold ${STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-600'}`}>
    {status.replace('_', ' ')}
  </span>
);

const BugReportsPage: React.FC = () => {
  const { hasPermission: canView } = useHasPermission('CAN_VIEW_BUG_REPORTS');
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_BUG_REPORTS');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [submittedInfo, setSubmittedInfo] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [commentDrafts, setCommentDrafts] = useState<Record<number, string>>({});

  const { data: myReports } = useMyBugReports();
  const { data: allReports, isLoading } = useBugReportList(filterStatus, canView);
  const { submit, update } = useBugReportActions({
    onSubmitted: () => {
      setTitle('');
      setDescription('');
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setSubmittedInfo('Dziękujemy! Zgłoszenie zostało zapisane.');
    },
  });

  const submitReport = (event: React.FormEvent) => {
    event.preventDefault();
    if (!title.trim()) return;
    setSubmittedInfo('');
    submit.mutate({ title: title.trim(), description: description.trim(), file });
  };

  const changeStatus = (report: BugReport, status: BugReportStatus) => {
    update.mutate({ id: report.id, data: { status } });
  };

  const saveComment = (report: BugReport) => {
    const draft = commentDrafts[report.id];
    if (draft === undefined || draft === report.resolution_comment) return;
    update.mutate({ id: report.id, data: { resolution_comment: draft } });
  };

  const downloadFile = async (report: BugReport) => {
    try {
      await bugReportService.downloadFile(report);
    } catch {
      alert('Nie udało się pobrać pliku.');
    }
  };

  return (
    <PageShell>
      <div className="mb-6 flex items-center gap-3 border-b pb-4">
        <span className="text-2xl">🐛</span>
        <h1 className="text-xl font-bold text-gray-900 uppercase">Zgłoszenia błędów</h1>
      </div>

      {/* ── Submit form: every logged-in user ── */}
      <form onSubmit={submitReport} className="mb-8 max-w-2xl space-y-4">
        <h2 className="text-sm font-black uppercase text-gray-400">Zgłoś błąd</h2>
        <div>
          <label htmlFor="bug-title" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Tytuł *
          </label>
          <input
            id="bug-title"
            type="text"
            value={title}
            required
            maxLength={200}
            placeholder="Co nie działa?"
            onChange={(e) => setTitle(e.target.value)}
            className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
          />
        </div>
        <div>
          <label htmlFor="bug-description" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Opis
          </label>
          <textarea
            id="bug-description"
            value={description}
            maxLength={5000}
            placeholder="Kroki do odtworzenia, co się stało, czego się spodziewałeś..."
            onChange={(e) => setDescription(e.target.value)}
            className="min-h-24 w-full resize-y rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
          />
        </div>
        <div>
          <label htmlFor="bug-file" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Załącznik (zrzut ekranu, log — do 10 MB)
          </label>
          <input
            id="bug-file"
            ref={fileInputRef}
            type="file"
            accept={BUG_REPORT_ACCEPT}
            onChange={(e) => setFile(e.currentTarget.files?.[0] ?? null)}
            className="min-h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-600 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-1 file:text-sm file:font-bold file:text-indigo-700"
          />
        </div>
        {submittedInfo && (
          <p className="rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700">
            {submittedInfo}
          </p>
        )}
        <button
          type="submit"
          disabled={!title.trim() || submit.isPending}
          className="min-h-10 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white transition-all hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
        >
          {submit.isPending ? 'Wysyłanie...' : 'Wyślij zgłoszenie'}
        </button>
      </form>

      {/* ── My reports ── */}
      {!!myReports?.length && (
        <div className="mb-8">
          <h2 className="mb-3 text-sm font-black uppercase text-gray-400">Moje zgłoszenia</h2>
          <div className="space-y-2">
            {myReports.map((report) => (
              <div key={report.id} className="rounded-lg border border-gray-200 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-bold text-gray-900">{report.title}</p>
                  <StatusBadge status={report.status} />
                </div>
                <p className="mt-1 text-xs font-medium text-gray-400">{formatDate(report.created_at)}</p>
                {report.resolution_comment && (
                  <p className="mt-2 rounded bg-gray-50 px-3 py-2 text-sm font-medium text-gray-600">
                    Odpowiedź: {report.resolution_comment}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Developer view ── */}
      {canView && (
        <div>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-black uppercase text-gray-400">Wszystkie zgłoszenia</h2>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
            >
              <option value="">Wszystkie statusy</option>
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {status.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          {isLoading ? (
            <p className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">Ładowanie...</p>
          ) : !allReports?.length ? (
            <p className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">Brak zgłoszeń</p>
          ) : (
            <div className="space-y-3">
              {allReports.map((report) => (
                <div key={report.id} className="rounded-lg border border-gray-200 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-bold text-gray-900">{report.title}</p>
                      <p className="mt-1 text-xs font-medium text-gray-400">
                        {report.reporter_email || '—'} · {formatDate(report.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {report.original_filename && (
                        <button
                          type="button"
                          onClick={() => downloadFile(report)}
                          className="min-h-9 rounded-md bg-indigo-50 px-3 text-xs font-bold text-indigo-700 transition-colors hover:bg-indigo-100"
                        >
                          📎 {report.original_filename}
                        </button>
                      )}
                      {canManage ? (
                        <select
                          value={report.status}
                          disabled={update.isPending}
                          onChange={(e) => changeStatus(report, e.target.value as BugReportStatus)}
                          className="h-9 rounded-lg border border-gray-200 bg-gray-50 px-2 text-xs font-bold text-gray-600 outline-none focus:border-indigo-500"
                        >
                          {STATUS_OPTIONS.map((status) => (
                            <option key={status} value={status}>
                              {status.replace('_', ' ')}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <StatusBadge status={report.status} />
                      )}
                    </div>
                  </div>

                  {report.description && (
                    <p className="mt-3 whitespace-pre-wrap text-sm font-medium text-gray-700">{report.description}</p>
                  )}

                  {canManage && (
                    <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                      <input
                        type="text"
                        maxLength={2000}
                        placeholder="Komentarz do rozwiązania..."
                        value={commentDrafts[report.id] ?? report.resolution_comment}
                        onChange={(e) =>
                          setCommentDrafts((current) => ({ ...current, [report.id]: e.target.value }))
                        }
                        className="h-10 flex-1 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
                      />
                      <button
                        type="button"
                        disabled={
                          update.isPending ||
                          (commentDrafts[report.id] ?? report.resolution_comment) === report.resolution_comment
                        }
                        onClick={() => saveComment(report)}
                        className="min-h-10 rounded-lg bg-indigo-600 px-4 text-sm font-bold text-white transition-all hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
                      >
                        Zapisz komentarz
                      </button>
                    </div>
                  )}
                  {!canManage && report.resolution_comment && (
                    <p className="mt-2 rounded bg-gray-50 px-3 py-2 text-sm font-medium text-gray-600">
                      Odpowiedź: {report.resolution_comment}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
};

export default BugReportsPage;
