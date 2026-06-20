interface CsvColumn<T> {
  header: string;
  value: (row: T) => string | number | boolean | null | undefined;
}

const escapeCsvValue = (value: string | number | boolean | null | undefined) => {
  const text = value == null ? '' : String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

export function exportRowsToCsv<T>(filename: string, columns: CsvColumn<T>[], rows: T[]) {
  const header = columns.map((column) => escapeCsvValue(column.header)).join(',');
  const body = rows.map((row) => columns.map((column) => escapeCsvValue(column.value(row))).join(','));
  const csv = `\uFEFF${[header, ...body].join('\n')}`;
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
