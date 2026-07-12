import apiClient from '@/lib/api';
import type {
  BeneficiaryRecruitmentForm,
  BeneficiaryRecruitmentSubmission,
  RecruitmentField,
  RecruitmentFieldDraft,
} from '@/types';

const path = 'v1/beneficiary-recruitment';
const pageSize = 1000;
const headers = (token: string) => ({ headers: { 'X-Beneficiary-Recruitment-Token': token } });

export const beneficiaryRecruitmentService = {
  getForm: async (token: string): Promise<BeneficiaryRecruitmentForm> => {
    const response = await apiClient.get<BeneficiaryRecruitmentForm>(`${path}/public/form`, headers(token));
    return response.data;
  },
  submit: async (token: string, formToken: string, answers: Record<string, unknown>, website = ''): Promise<BeneficiaryRecruitmentSubmission> => {
    const response = await apiClient.post<BeneficiaryRecruitmentSubmission>(
      `${path}/public/submissions`,
      { answers, form_token: formToken, website },
      headers(token),
    );
    return response.data;
  },
  getAccessLink: async (): Promise<string> => (await apiClient.get<{ path: string }>(`${path}/access-link`)).data.path,
  getFields: async (): Promise<RecruitmentField[]> => (await apiClient.get<RecruitmentField[]>(`${path}/fields`)).data,
  saveFields: async (fields: RecruitmentFieldDraft[]): Promise<RecruitmentField[]> => (
    await apiClient.put<RecruitmentField[]>(`${path}/fields`, { fields })
  ).data,
  getSubmissions: async (includeArchived: boolean): Promise<BeneficiaryRecruitmentSubmission[]> => {
    const rows: BeneficiaryRecruitmentSubmission[] = [];
    let skip = 0;
    while (true) {
      const response = await apiClient.get<BeneficiaryRecruitmentSubmission[]>(`${path}/submissions`, {
        params: { include_archived: includeArchived, skip, limit: pageSize },
      });
      rows.push(...response.data);
      if (response.data.length < pageSize) return rows;
      skip += pageSize;
    }
  },
  createBeneficiary: async (id: number): Promise<BeneficiaryRecruitmentSubmission> => (
    await apiClient.post<BeneficiaryRecruitmentSubmission>(`${path}/submissions/${id}/create-beneficiary`, { group_id: null })
  ).data,
  reject: async (id: number, comment: string | null): Promise<BeneficiaryRecruitmentSubmission> => (
    await apiClient.post<BeneficiaryRecruitmentSubmission>(`${path}/submissions/${id}/reject`, { comment })
  ).data,
  archive: async (id: number): Promise<BeneficiaryRecruitmentSubmission> => (
    await apiClient.post<BeneficiaryRecruitmentSubmission>(`${path}/submissions/${id}/archive`)
  ).data,
  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`${path}/submissions/${id}`);
  },
};
