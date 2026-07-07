import apiClient from '@/lib/api';
import type { BugReport, BugReportSubmitInput, BugReportUpdateInput } from '@/types';

export const BUG_REPORT_ACCEPT = '.pdf,.jpg,.jpeg,.png,.webp,.heic,.heif,.txt,.log,.zip';
export const BUG_REPORT_MAX_SIZE_BYTES = 10 * 1024 * 1024;

export const bugReportService = {
  submit: async ({ title, description, file }: BugReportSubmitInput): Promise<BugReport> => {
    const form = new FormData();
    form.append('title', title);
    form.append('description', description);
    if (file) form.append('file', file);
    const response = await apiClient.post<BugReport>('v1/bug-reports', form);
    return response.data;
  },

  list: async (status?: string): Promise<BugReport[]> => {
    const response = await apiClient.get<BugReport[]>('v1/bug-reports', {
      params: status ? { status } : undefined,
    });
    return response.data;
  },

  listMine: async (): Promise<BugReport[]> => {
    const response = await apiClient.get<BugReport[]>('v1/bug-reports/my');
    return response.data;
  },

  update: async (id: number, data: BugReportUpdateInput): Promise<BugReport> => {
    const response = await apiClient.patch<BugReport>(`v1/bug-reports/${id}`, data);
    return response.data;
  },

  downloadFile: async (report: BugReport): Promise<void> => {
    const response = await apiClient.get<Blob>(`v1/bug-reports/${report.id}/file`, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], { type: report.content_type ?? 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = report.original_filename ?? 'zalacznik';
    link.click();
    URL.revokeObjectURL(url);
  },
};
