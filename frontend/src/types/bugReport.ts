export type BugReportStatus = 'NOWY' | 'W_TRAKCIE' | 'ROZWIĄZANY' | 'ODRZUCONY';

export interface BugReport {
  id: number;
  title: string;
  description: string;
  status: BugReportStatus;
  resolution_comment: string;
  reporter_id: number | null;
  reporter_email: string;
  original_filename: string | null;
  content_type: string | null;
  size_bytes: number | null;
  created_at: string;
  updated_at: string;
}

export interface BugReportSubmitInput {
  title: string;
  description: string;
  file: File | null;
}

export interface BugReportUpdateInput {
  status?: BugReportStatus;
  resolution_comment?: string;
}
