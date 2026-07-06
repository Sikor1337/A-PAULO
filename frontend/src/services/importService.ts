import apiClient from '@/lib/api';
import type { ImportEntity, ImportReport } from '@/types';

const TEMPLATE_FILENAMES: Record<ImportEntity, string> = {
  volunteers: 'formatka-wolontariusze.csv',
  beneficiaries: 'formatka-podopieczni.csv',
};

export const importService = {
  downloadTemplate: async (entity: ImportEntity): Promise<void> => {
    const response = await apiClient.get<Blob>(`v1/imports/${entity}/template`, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = TEMPLATE_FILENAMES[entity];
    link.click();
    URL.revokeObjectURL(url);
  },

  importCsv: async (entity: ImportEntity, file: File): Promise<ImportReport> => {
    const form = new FormData();
    form.append('file', file);
    const response = await apiClient.post<ImportReport>(`v1/imports/${entity}`, form);
    return response.data;
  },
};
