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

/** Generic sortable table with the shared dark header, hover rows and loading/empty states. */
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

  return (
    <div className="overflow-x-auto border rounded-lg">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-[#1e2330] text-white text-xs uppercase font-bold tracking-wider">
            {columns.map((col, i) => {
              const borderR = i !== lastIndex ? 'border-r border-gray-700' : '';
              const alignCls = col.align === 'center' ? 'text-center' : '';
              const sortable = col.sortKey
                ? 'cursor-pointer select-none'
                : '';
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
              <tr key={getRowKey(row)} className="hover:bg-blue-50 border-b last:border-0 transition-colors">
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
  );
}

export default DataTable;
