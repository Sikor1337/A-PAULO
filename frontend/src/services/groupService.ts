import apiClient from '@/lib/api';
import { createCrudService } from './crudService';
import type { GroupListItem, GroupDetail, GroupSaveInput, BeneficiaryAssignment } from '@/types';

const crud = createCrudService<GroupListItem, GroupSaveInput>('v1/groups');

export const groupService = {
  ...crud,

  // getById returns the richer detail shape (with nested beneficiaries).
  getById: async (id: number): Promise<GroupDetail> => {
    const response = await apiClient.get<GroupDetail>(`v1/groups/${id}`);
    return response.data;
  },

  // ── Assignments ──
  getAssignments: async (): Promise<BeneficiaryAssignment[]> => {
    const response = await apiClient.get<BeneficiaryAssignment[]>('v1/groups/assignments');
    return response.data;
  },

  createAssignment: async (data: { beneficiary: number; volunteer: number }): Promise<BeneficiaryAssignment> => {
    const response = await apiClient.post<BeneficiaryAssignment>('v1/groups/assignments', data);
    return response.data;
  },

  deleteAssignment: async (id: number): Promise<void> => {
    await apiClient.delete(`v1/groups/assignments/${id}`);
  },
};
