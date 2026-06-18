import { useMemo, useState } from 'react';

export type SortDir = 'asc' | 'desc';

interface Options<T> {
  /** Fields scanned by the free-text search box. */
  searchFields: (keyof T)[];
  /** Column the list is sorted by initially. */
  initialSort: keyof T;
  /** Optional custom comparators for non-string columns (e.g. booleans). */
  comparators?: Partial<Record<keyof T, (a: T, b: T) => number>>;
  /** Extra row predicate driven by page-level filters (group/status/BO…). */
  filterPredicate?: (row: T) => boolean;
}

/**
 * Encapsulates the search + sort logic shared by every list table:
 * free-text filtering, an injectable filter predicate, and toggleable column sorting.
 */
export function useTableControls<T>(rows: T[] | undefined, options: Options<T>) {
  const { searchFields, initialSort, comparators, filterPredicate } = options;
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<keyof T>(initialSort);
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const toggleSort = (key: keyof T) => {
    if (sortKey === key) setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortIcon = (key: keyof T): string => (sortKey !== key ? ' ↕' : sortDir === 'asc' ? ' ↑' : ' ↓');

  const visibleRows = useMemo(() => {
    if (!rows) return [];
    const term = search.toLowerCase();

    let filtered = rows.filter((row) =>
      searchFields.some((field) => String(row[field] ?? '').toLowerCase().includes(term)),
    );
    if (filterPredicate) filtered = filtered.filter(filterPredicate);

    const comparator = comparators?.[sortKey];
    const sorted = [...filtered].sort((a, b) => {
      const cmp = comparator
        ? comparator(a, b)
        : String(a[sortKey] ?? '').toLowerCase().localeCompare(String(b[sortKey] ?? '').toLowerCase());
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return sorted;
  }, [rows, search, sortKey, sortDir, searchFields, comparators, filterPredicate]);

  return { search, setSearch, sortKey, sortDir, toggleSort, sortIcon, rows: visibleRows };
}
