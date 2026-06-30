import apiClient from '@/lib/api';
import type {
  RecruitmentField,
  RecruitmentFieldDraft,
  RecruitmentForm,
  RecruitmentStatus,
  RecruitmentSubmission,
} from '@/types';

const path = 'v1/recruitment';
const pageSize = 1000;

async function fetchAll<T>(url: string, params: Record<string, unknown> = {}): Promise<T[]> {
  const rows: T[] = [];
  let skip = 0;
  while (true) {
    const response = await apiClient.get<T[]>(url, { params: { ...params, skip, limit: pageSize } });
    rows.push(...response.data);
    if (response.data.length < pageSize) return rows;
    skip += pageSize;
  }
}

export const recruitmentService = {
  getForm: async (): Promise<RecruitmentForm> => {
    const response = await apiClient.get<RecruitmentForm>(`${path}/form`);
    return response.data;
  },

  submit: async (answers: Record<string, unknown>): Promise<RecruitmentSubmission> => {
    const response = await apiClient.post<RecruitmentSubmission>(`${path}/submissions`, { answers });
    return response.data;
  },

  getFields: async (): Promise<RecruitmentField[]> => {
    const response = await apiClient.get<RecruitmentField[]>(`${path}/fields`);
    return response.data;
  },

  saveFields: async (fields: RecruitmentFieldDraft[]): Promise<RecruitmentField[]> => {
    const response = await apiClient.put<RecruitmentField[]>(`${path}/fields`, { fields });
    return response.data;
  },

  getSubmissions: async (status?: RecruitmentStatus): Promise<RecruitmentSubmission[]> => {
    return fetchAll(`${path}/submissions`, status ? { status } : {});
  },

  transition: async (
    id: number,
    action: 'start-onboarding' | 'return' | 'accept' | 'reject' | 'restore-onboarding',
    note?: string,
  ): Promise<RecruitmentSubmission> => {
    const body = action === 'return'
      ? { reason: note || null }
      : action === 'accept' || action === 'reject'
        ? { comment: note || null }
        : undefined;
    const response = await apiClient.post<RecruitmentSubmission>(
      `${path}/submissions/${id}/${action}`,
      body,
    );
    return response.data;
  },
};
