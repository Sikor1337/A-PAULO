import { useEffect, useMemo, useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import { useBOCardOverview, useBOCardOverviewActions } from '@/hooks/useAttachments';
import { useGroupList } from '@/hooks/useGroups';
import { formatDate } from '@/lib/date';
import { parseApiError } from '@/lib/errors';
import { attachmentService } from '@/services/attachmentService';
import type {
  BOCardOverviewAttachment,
  BOCardOverviewFilters,
  BOCardSortKey,
  SortDirection,
} from '@/types';

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const SORT_OPTIONS: Array<{
  value: string;
  label: string;
  sortBy: BOCardSortKey;
  sortDirection: SortDirection;
}> = [
  { value: 'created_at-desc', label: 'Najnowsze dodane', sortBy: 'created_at', sortDirection: 'desc' },
  { value: 'created_at-asc', label: 'Najstarsze dodane', sortBy: 'created_at', sortDirection: 'asc' },
  { value: 'period-desc', label: 'Okres: najnowszy', sortBy: 'period', sortDirection: 'desc' },
  { value: 'period-asc', label: 'Okres: najstarszy', sortBy: 'period', sortDirection: 'asc' },
  { value: 'group_name-asc', label: 'Grupa A-Z', sortBy: 'group_name', sortDirection: 'asc' },
  { value: 'beneficiary_name-asc', label: 'Podopieczny A-Z', sortBy: 'beneficiary_name', sortDirection: 'asc' },
  { value: 'volunteer_name-asc', label: 'Wolontariusz A-Z', sortBy: 'volunteer_name', sortDirection: 'asc' },
  { value: 'size_bytes-desc', label: 'Największe pliki', sortBy: 'size_bytes', sortDirection: 'desc' },
];

const formatSize = (sizeBytes: number) => {
  if (sizeBytes < 1024 * 1024) return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
};

const displayValue = (value?: string | null) => value || '—';

interface CommentEditorProps {
  attachment: BOCardOverviewAttachment;
  disabled: boolean;
  onSave: (attachment: BOCardOverviewAttachment, description: string) => void;
}

const CommentEditor = ({ attachment, disabled, onSave }: CommentEditorProps) => {
  const [value, setValue] = useState(attachment.description);

  const normalizedValue = value.trim();
  const isDirty = normalizedValue !== attachment.description;

  return (
    <div className="min-w-[220px] space-y-2">
      <textarea
        value={value}
        maxLength={1000}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Komentarz"
        className="min-h-16 w-full resize-y rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm leading-snug text-gray-700 outline-none focus:border-indigo-500"
      />
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] font-bold text-gray-300">{value.length}/1000</span>
        <button
          type="button"
          disabled={!isDirty || disabled}
          onClick={() => onSave(attachment, normalizedValue)}
          className="min-h-8 rounded-md bg-indigo-600 px-3 text-xs font-bold text-white transition-colors hover:bg-indigo-700 disabled:bg-gray-100 disabled:text-gray-300"
        >
          Zapisz
        </button>
      </div>
    </div>
  );
};

const BOCardsPage: React.FC = () => {
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [groupId, setGroupId] = useState<number | ''>('');
  const [periodFrom, setPeriodFrom] = useState('');
  const [periodTo, setPeriodTo] = useState('');
  const [hasComment, setHasComment] = useState<'' | 'yes' | 'no'>('');
  const [sortValue, setSortValue] = useState(SORT_OPTIONS[0].value);
  const [limit, setLimit] = useState(25);
  const [page, setPage] = useState(1);

  const { data: groups } = useGroupList();
  const selectedSort = SORT_OPTIONS.find((option) => option.value === sortValue) ?? SORT_OPTIONS[0];

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 350);
    return () => window.clearTimeout(timeoutId);
  }, [searchInput]);

  const filters: BOCardOverviewFilters = useMemo(
    () => ({
      search,
      groupId,
      periodFrom,
      periodTo,
      hasComment,
      sortBy: selectedSort.sortBy,
      sortDirection: selectedSort.sortDirection,
      page,
      limit,
    }),
    [groupId, hasComment, limit, page, periodFrom, periodTo, search, selectedSort.sortBy, selectedSort.sortDirection],
  );

  const { data, error, isError, isFetching, isLoading } = useBOCardOverview(filters);
  const { updateAttachment, deleteAttachment, downloadArchive } = useBOCardOverviewActions(filters);
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const start = total === 0 ? 0 : (page - 1) * limit + 1;
  const end = Math.min(page * limit, total);

  const setFirstPage = () => setPage(1);

  const resetFilters = () => {
    setSearchInput('');
    setSearch('');
    setGroupId('');
    setPeriodFrom('');
    setPeriodTo('');
    setHasComment('');
    setSortValue(SORT_OPTIONS[0].value);
    setLimit(25);
    setPage(1);
  };

  const saveComment = (attachment: BOCardOverviewAttachment, description: string) => {
    updateAttachment.mutate({ id: attachment.id, data: { description } });
  };

  const openAttachment = async (attachment: BOCardOverviewAttachment) => {
    try {
      await attachmentService.openContent(attachment);
    } catch {
      alert('Nie udało się otworzyć pliku.');
    }
  };

  const removeAttachment = (attachment: BOCardOverviewAttachment) => {
    if (!confirm(`Usunąć plik „${attachment.display_name}”?`)) return;
    deleteAttachment.mutate(attachment.id, {
      onSuccess: () => {
        if (items.length === 1 && page > 1) setPage((current) => current - 1);
      },
    });
  };

  const actionDisabled = updateAttachment.isPending || deleteAttachment.isPending;

  return (
    <PageShell>
      <div className="mb-5 flex flex-col gap-4 border-b pb-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">BO</span>
          <div>
            <h1 className="text-xl font-bold uppercase text-gray-900">Karty BO</h1>
            <p className="text-xs font-semibold text-gray-400">{total} wyników</p>
          </div>
          {isFetching && <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-bold text-amber-700">Odświeżanie</span>}
        </div>

        <div className="grid grid-cols-2 gap-2 sm:flex">
          <button
            type="button"
            onClick={() => downloadArchive.mutate()}
            disabled={total === 0 || downloadArchive.isPending}
            className="min-h-10 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-emerald-700 disabled:bg-gray-100 disabled:text-gray-300"
          >
            {downloadArchive.isPending ? 'Pobieranie...' : 'Pobierz ZIP'}
          </button>
          <button
            type="button"
            onClick={resetFilters}
            className="min-h-10 rounded-lg border border-gray-200 px-4 py-2 text-sm font-bold text-gray-600 transition-colors hover:bg-gray-50"
          >
            Wyczyść
          </button>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-[minmax(220px,1fr)_180px_150px_150px_150px_180px_110px]">
        <input
          type="text"
          placeholder="Szukaj pliku, osoby, grupy, komentarza..."
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-4 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
        />
        <select
          value={groupId}
          onChange={(event) => {
            setGroupId(event.target.value === '' ? '' : Number(event.target.value));
            setFirstPage();
          }}
          className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
        >
          <option value="">Wszystkie grupy</option>
          {groups?.map((group) => (
            <option key={group.id} value={group.id}>
              {group.name}
            </option>
          ))}
        </select>
        <input
          type="month"
          value={periodFrom}
          onChange={(event) => {
            setPeriodFrom(event.target.value);
            setFirstPage();
          }}
          className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
          aria-label="Okres od"
        />
        <input
          type="month"
          value={periodTo}
          onChange={(event) => {
            setPeriodTo(event.target.value);
            setFirstPage();
          }}
          className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
          aria-label="Okres do"
        />
        <select
          value={hasComment}
          onChange={(event) => {
            setHasComment(event.target.value as '' | 'yes' | 'no');
            setFirstPage();
          }}
          className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
        >
          <option value="">Komentarz: wszystkie</option>
          <option value="yes">Z komentarzem</option>
          <option value="no">Bez komentarza</option>
        </select>
        <select
          value={sortValue}
          onChange={(event) => {
            setSortValue(event.target.value);
            setFirstPage();
          }}
          className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select
          value={limit}
          onChange={(event) => {
            setLimit(Number(event.target.value));
            setFirstPage();
          }}
          className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
        >
          {PAGE_SIZE_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}/str.
            </option>
          ))}
        </select>
      </div>

      {isError && (
        <div className="mb-4 rounded-lg border border-rose-100 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {parseApiError(error)}
        </div>
      )}

      <div className="space-y-3 md:hidden">
        {isLoading ? (
          <div className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">Ładowanie...</div>
        ) : items.length === 0 ? (
          <div className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">Brak kart BO</div>
        ) : (
          items.map((attachment) => (
            <article key={attachment.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-bold text-gray-900">{attachment.display_name}</p>
                  <p className="mt-1 text-xs font-semibold text-gray-400">
                    {displayValue(attachment.period)} · {formatSize(attachment.size_bytes)}
                  </p>
                </div>
                <span className="rounded-md bg-indigo-50 px-2 py-1 text-[10px] font-bold text-indigo-600">
                  {displayValue(attachment.group_name)}
                </span>
              </div>

              <dl className="grid grid-cols-[100px_1fr] gap-x-3 gap-y-2 text-sm">
                <dt className="text-[10px] font-black uppercase text-gray-400">Podopieczny</dt>
                <dd className="min-w-0 font-semibold text-gray-700">{displayValue(attachment.beneficiary_name)}</dd>
                <dt className="text-[10px] font-black uppercase text-gray-400">Wolontariusz</dt>
                <dd className="min-w-0 font-semibold text-gray-700">{displayValue(attachment.volunteer_name)}</dd>
                <dt className="text-[10px] font-black uppercase text-gray-400">Dodano</dt>
                <dd className="font-semibold text-gray-500">{formatDate(attachment.created_at)}</dd>
              </dl>

              <div className="mt-4">
                <CommentEditor
                  key={`${attachment.id}-${attachment.description}`}
                  attachment={attachment}
                  disabled={actionDisabled}
                  onSave={saveComment}
                />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => openAttachment(attachment)}
                  className="min-h-10 rounded-lg bg-indigo-50 px-3 text-sm font-bold text-indigo-700 transition-colors hover:bg-indigo-100"
                >
                  Podgląd
                </button>
                <button
                  type="button"
                  disabled={actionDisabled}
                  onClick={() => removeAttachment(attachment)}
                  className="min-h-10 rounded-lg bg-rose-50 px-3 text-sm font-bold text-rose-700 transition-colors hover:bg-rose-100 disabled:opacity-50"
                >
                  Usuń
                </button>
              </div>
            </article>
          ))
        )}
      </div>

      <div className="hidden overflow-x-auto rounded-lg border border-gray-200 md:block">
        <table className="w-full min-w-[1180px] border-collapse text-left text-sm">
          <thead>
            <tr className="bg-[#1e2330] text-[10px] font-bold uppercase tracking-widest text-white">
              <th className="w-[20%] border-r border-white/10 px-3 py-3">Karta</th>
              <th className="w-[14%] border-r border-white/10 px-3 py-3">Grupa</th>
              <th className="w-[17%] border-r border-white/10 px-3 py-3">Podopieczny</th>
              <th className="w-[17%] border-r border-white/10 px-3 py-3">Wolontariusz</th>
              <th className="w-[8%] border-r border-white/10 px-3 py-3">Okres</th>
              <th className="w-[19%] border-r border-white/10 px-3 py-3">Komentarz</th>
              <th className="w-[5%] px-3 py-3 text-center">Akcje</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="p-10 text-center text-gray-400">Ładowanie...</td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-10 text-center text-gray-400">Brak kart BO</td>
              </tr>
            ) : (
              items.map((attachment) => (
                <tr key={attachment.id} className="border-b border-gray-100 align-top last:border-0 hover:bg-amber-50/40">
                  <td className="border-r border-gray-100 px-3 py-3">
                    <p className="font-bold leading-tight text-gray-900">{attachment.display_name}</p>
                    <p className="mt-1 text-xs font-semibold text-gray-400">{attachment.original_filename}</p>
                    <p className="mt-2 text-[11px] font-semibold text-gray-400">
                      {formatSize(attachment.size_bytes)} · {formatDate(attachment.created_at)}
                    </p>
                  </td>
                  <td className="border-r border-gray-100 px-3 py-3 font-semibold text-gray-700">{displayValue(attachment.group_name)}</td>
                  <td className="border-r border-gray-100 px-3 py-3 font-semibold text-indigo-700">{displayValue(attachment.beneficiary_name)}</td>
                  <td className="border-r border-gray-100 px-3 py-3 font-semibold text-gray-700">{displayValue(attachment.volunteer_name)}</td>
                  <td className="border-r border-gray-100 px-3 py-3 font-bold text-gray-600">{displayValue(attachment.period)}</td>
                  <td className="border-r border-gray-100 px-3 py-3">
                    <CommentEditor
                      key={`${attachment.id}-${attachment.description}`}
                      attachment={attachment}
                      disabled={actionDisabled}
                      onSave={saveComment}
                    />
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-col gap-2">
                      <button
                        type="button"
                        onClick={() => openAttachment(attachment)}
                        className="min-h-9 rounded-md bg-indigo-50 px-3 text-xs font-bold text-indigo-700 transition-colors hover:bg-indigo-100"
                      >
                        Podgląd
                      </button>
                      <button
                        type="button"
                        disabled={actionDisabled}
                        onClick={() => removeAttachment(attachment)}
                        className="min-h-9 rounded-md bg-rose-50 px-3 text-xs font-bold text-rose-700 transition-colors hover:bg-rose-100 disabled:opacity-50"
                      >
                        Usuń
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm font-semibold text-gray-400">
          {start}-{end} z {total}
        </p>
        <div className="grid grid-cols-2 gap-2 sm:flex sm:items-center">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            className="min-h-10 rounded-lg border border-gray-200 px-4 text-sm font-bold text-gray-600 transition-colors hover:bg-gray-50 disabled:text-gray-300"
          >
            Poprzednia
          </button>
          <span className="flex min-h-10 items-center justify-center rounded-lg bg-gray-50 px-4 text-sm font-bold text-gray-500">
            {page} / {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            className="min-h-10 rounded-lg border border-gray-200 px-4 text-sm font-bold text-gray-600 transition-colors hover:bg-gray-50 disabled:text-gray-300"
          >
            Następna
          </button>
        </div>
      </div>
    </PageShell>
  );
};

export default BOCardsPage;
