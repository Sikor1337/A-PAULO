import apiClient from '@/lib/api';
import type {
  RecruitmentField,
  RecruitmentFieldInput,
  RecruitmentForm,
  RecruitmentInvitation,
  RecruitmentInvitationInput,
  RecruitmentPublicForm,
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

  getInvitedForm: async (token: string): Promise<RecruitmentPublicForm> => {
    const response = await apiClient.get<RecruitmentPublicForm>(`${path}/form/${token}`);
    return response.data;
  },

  submit: async (token: string, answers: Record<string, unknown>): Promise<RecruitmentSubmission> => {
    const response = await apiClient.post<RecruitmentSubmission>(`${path}/submissions/${token}`, { answers });
    return response.data;
  },

  getFields: async (): Promise<RecruitmentField[]> => {
    const response = await apiClient.get<RecruitmentField[]>(`${path}/fields`);
    return response.data;
  },

  createField: async (data: RecruitmentFieldInput): Promise<RecruitmentField> => {
    const response = await apiClient.post<RecruitmentField>(`${path}/fields`, data);
    return response.data;
  },

  updateField: async (id: number, data: Partial<RecruitmentFieldInput>): Promise<RecruitmentField> => {
    const response = await apiClient.patch<RecruitmentField>(`${path}/fields/${id}`, data);
    return response.data;
  },

  deleteField: async (id: number): Promise<void> => {
    await apiClient.delete(`${path}/fields/${id}`);
  },

  reorderFields: async (fieldIds: number[]): Promise<RecruitmentField[]> => {
    const response = await apiClient.put<RecruitmentField[]>(`${path}/fields/order`, { field_ids: fieldIds });
    return response.data;
  },

  getInvitations: async (): Promise<RecruitmentInvitation[]> => fetchAll(`${path}/invitations`),

  createInvitation: async (data: RecruitmentInvitationInput): Promise<RecruitmentInvitation> => {
    const response = await apiClient.post<RecruitmentInvitation>(`${path}/invitations`, data);
    return response.data;
  },

  revokeInvitation: async (id: number): Promise<void> => {
    await apiClient.delete(`${path}/invitations/${id}`);
  },

  getSubmissions: async (status?: RecruitmentStatus): Promise<RecruitmentSubmission[]> => {
    return fetchAll(`${path}/submissions`, status ? { status } : {});
  },

  transition: async (
    id: number,
    action: 'start-onboarding' | 'return' | 'accept' | 'reject',
    reason?: string,
  ): Promise<RecruitmentSubmission> => {
    const response = await apiClient.post<RecruitmentSubmission>(
      `${path}/submissions/${id}/${action}`,
      action === 'return' ? { reason: reason || null } : undefined,
    );
    return response.data;
  },
};
