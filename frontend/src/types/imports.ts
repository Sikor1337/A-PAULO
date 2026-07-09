export type ImportEntity = 'volunteers' | 'beneficiaries';

export interface ImportRowIssue {
  /** CSV file line number (header is line 1). */
  row: number;
  message: string;
}

export interface ImportReport {
  ok: boolean;
  total_rows: number;
  imported: number;
  skipped: ImportRowIssue[];
  errors: ImportRowIssue[];
}
