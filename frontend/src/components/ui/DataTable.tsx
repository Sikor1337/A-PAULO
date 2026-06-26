import type { Key, ReactNode } from 'react';

export interface Column<T> {
  /** Stable column identity (also used as React key). */
  id: string;
  header: ReactNode;
  /** Width utility class, e.g. "w-[20%]". */
  widthClass?: string;
  align?: 'left' | 'center';
  /** When set, the header becomes a sort toggle for this field. */
  sortKey?: keyof T;
  /** Extra classes for the body cell (<td>). */
  cellClassName?: string;
  /** Click handler attached to this body cell (e.g. open details). */
  onClick?: (row: T) => void;
  /** Optional mobile label when the desktop header is not text. */
  mobileLabel?: string;
  /** Hide supporting columns from the mobile card layout. */
  hideOnMobile?: boolean;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  isLoading: boolean;
  getRowKey: (row: T) => Key;
  toggleSort: (key: keyof T) => void;
  sortIcon: (key: keyof T) => string;
  emptyText?: string;
}

const headerLabel = <T,>(column: Column<T>) => {
  if (column.mobileLabel) return column.mobileLabel;
  if (typeof column.header === 'string' || typeof column.header === 'number') return String(column.header);
  return '';
};

/** Generic sortable table. On phones, rows are rendered as labeled cards instead of a squeezed table. */
function DataTable<T>({
  columns,
  rows,
  isLoading,
  getRowKey,
  toggleSort,
  sortIcon,
  emptyText = 'Brak wyników',
}: DataTableProps<T>) {
  const lastIndex = columns.length - 1;
  const mobileColumns = columns.filter((column) => !column.hideOnMobile);

  return (
    <>
      <div className="space-y-3 md:hidden">
        {isLoading ? (
          <div className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">
            Ładowanie...
          </div>
        ) : rows.length === 0 ? (
          <div className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">
            {emptyText}
          </div>
        ) : (
          rows.map((row) => (
            <article key={getRowKey(row)} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              {mobileColumns.map((col) => {
                const isActions = col.id === 'actions';
                const label = headerLabel(col);

                if (isActions) {
                  return (
                    <div key={col.id} className="mt-3 border-t border-gray-100 pt-3">
                      {col.render(row)}
                    </div>
                  );
                }

                return (
                  <div key={col.id} className="grid grid-cols-[minmax(92px,38%)_1fr] gap-3 border-b border-gray-100 py-2 last:border-b-0">
                    <dt className="text-[10px] font-black uppercase text-gray-400">{label}</dt>
                    <dd
                      className={`min-w-0 text-sm leading-snug ${col.align === 'center' ? 'text-left' : ''} ${
                        col.cellClassName ?? ''
                      }`}
                      onClick={col.onClick ? () => col.onClick!(row) : undefined}
                    >
                      {col.render(row)}
                    </dd>
                  </div>
                );
              })}
            </article>
          ))
        )}
      </div>

      <div className="hidden overflow-x-auto rounded-lg border md:block">
        <table className="w-full min-w-[760px] border-collapse text-left">
          <thead>
            <tr className="bg-[#1e2330] text-xs font-bold uppercase tracking-wider text-white">
              {columns.map((col, i) => {
                const borderR = i !== lastIndex ? 'border-r border-gray-700' : '';
                const alignCls = col.align === 'center' ? 'text-center' : '';
                const sortable = col.sortKey ? 'cursor-pointer select-none' : '';
                return (
                  <th
                    key={col.id}
                    className={`p-3 ${col.widthClass ?? ''} ${borderR} ${alignCls} ${sortable}`}
                    onClick={col.sortKey ? () => toggleSort(col.sortKey as keyof T) : undefined}
                  >
                    {col.header}
                    {col.sortKey ? sortIcon(col.sortKey) : ''}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="text-sm">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length} className="p-10 text-center text-gray-400">
                  Ładowanie...
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="p-10 text-center text-gray-400">
                  {emptyText}
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={getRowKey(row)} className="border-b transition-colors last:border-0 hover:bg-blue-50">
                  {columns.map((col, i) => {
                    const borderR = i !== lastIndex ? 'border-r' : '';
                    const alignCls = col.align === 'center' ? 'text-center' : '';
                    return (
                      <td
                        key={col.id}
                        className={`p-3 ${borderR} ${alignCls} ${col.cellClassName ?? ''}`}
                        onClick={col.onClick ? () => col.onClick!(row) : undefined}
                      >
                        {col.render(row)}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default DataTable;
