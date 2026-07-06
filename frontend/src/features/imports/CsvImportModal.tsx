import { useRef, useState } from 'react';
import Modal from '@/components/ui/Modal';
import { useCsvImport } from '@/hooks/useCsvImport';
import { importService } from '@/services/importService';
import { parseApiError } from '@/lib/errors';
import type { ImportEntity, ImportReport, ImportRowIssue } from '@/types';

interface CsvImportModalProps {
  entity: ImportEntity;
  /** Entity name for copy, e.g. "wolontariuszy". */
  entityLabel: string;
  onClose: () => void;
}

const IssueList = ({ title, issues, className }: { title: string; issues: ImportRowIssue[]; className: string }) => {
  if (issues.length === 0) return null;
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${className}`}>
      <p className="mb-1 font-bold">{title}</p>
      <ul className="max-h-40 space-y-1 overflow-y-auto">
        {issues.map((issue, index) => (
          <li key={`${issue.row}-${index}`} className="font-medium">
            Wiersz {issue.row}: {issue.message}
          </li>
        ))}
      </ul>
    </div>
  );
};

/** Shared CSV import dialog: template download, file upload, per-row report. */
const CsvImportModal = ({ entity, entityLabel, onClose }: CsvImportModalProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState('');
  const importCsv = useCsvImport(entity);

  const downloadTemplate = async () => {
    try {
      await importService.downloadTemplate(entity);
    } catch (err) {
      setError(parseApiError(err));
    }
  };

  const selectFile = (files: FileList | null) => {
    setFile(files?.[0] ?? null);
    setReport(null);
    setError('');
  };

  const runImport = () => {
    if (!file) return;
    setError('');
    importCsv.mutate(file, {
      onSuccess: (result) => {
        setReport(result);
        if (result.ok && fileInputRef.current) {
          fileInputRef.current.value = '';
          setFile(null);
        }
      },
      onError: (err) => setError(parseApiError(err)),
    });
  };

  return (
    <Modal onClose={onClose}>
      <div className="mb-6 flex items-start justify-between gap-4">
        <h2 className="text-xl font-bold text-gray-900">Import {entityLabel} z CSV</h2>
        <button onClick={onClose} className="text-2xl leading-none text-gray-400 hover:text-gray-600">
          &times;
        </button>
      </div>

      <ol className="mb-5 list-decimal space-y-1 pl-5 text-sm font-medium text-gray-600">
        <li>Pobierz formatkę i wklej dane (separator „;” lub „,”, daty RRRR-MM-DD).</li>
        <li>Wybierz zapisany plik CSV i kliknij „Importuj”.</li>
        <li>Plik z błędami nie jest importowany — popraw wiersze z raportu i wgraj ponownie.</li>
      </ol>

      <div className="mb-4 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          onClick={downloadTemplate}
          className="min-h-10 rounded-lg border border-gray-200 px-4 py-2 text-sm font-bold text-gray-600 transition-all hover:bg-gray-50"
        >
          Pobierz formatkę
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => selectFile(event.currentTarget.files)}
          className="min-h-10 flex-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-600 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-1 file:text-sm file:font-bold file:text-indigo-700"
        />
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-rose-100 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      {report && (
        <div className="mb-4 space-y-3">
          <div
            className={`rounded-lg border px-4 py-3 text-sm font-bold ${
              report.ok ? 'border-emerald-100 bg-emerald-50 text-emerald-700' : 'border-rose-100 bg-rose-50 text-rose-700'
            }`}
          >
            {report.ok
              ? `Zaimportowano ${report.imported} z ${report.total_rows} wierszy.`
              : `Import zatrzymany — plik zawiera błędy (${report.errors.length}). Nic nie zostało zaimportowane.`}
          </div>
          <IssueList
            title="Błędy"
            issues={report.errors}
            className="border-rose-100 bg-rose-50 text-rose-700"
          />
          <IssueList
            title="Pominięte duplikaty"
            issues={report.skipped}
            className="border-amber-100 bg-amber-50 text-amber-700"
          />
        </div>
      )}

      <div className="flex flex-col-reverse gap-2 border-t pt-5 sm:flex-row sm:justify-end sm:gap-3">
        <button onClick={onClose} className="px-4 py-2 font-bold text-gray-400">
          Zamknij
        </button>
        <button
          type="button"
          disabled={!file || importCsv.isPending}
          onClick={runImport}
          className="min-h-10 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white transition-all hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
        >
          {importCsv.isPending ? 'Importowanie...' : 'Importuj'}
        </button>
      </div>
    </Modal>
  );
};

export default CsvImportModal;
