import apiClient from '@/lib/api';
import type {
  DepartmentDetail,
  DepartmentInput,
  DepartmentInventoryItem,
  DepartmentInventoryItemInput,
  DepartmentListItem,
} from '@/types';

export const departmentService = {
  list: async (includeArchived = false): Promise<DepartmentListItem[]> => {
    const response = await apiClient.get<DepartmentListItem[]>('v1/departments', {
      params: includeArchived ? { include_archived: true } : undefined,
    });
    return response.data;
  },

  get: async (id: number): Promise<DepartmentDetail> => {
    const response = await apiClient.get<DepartmentDetail>(`v1/departments/${id}`);
    return response.data;
  },

  create: async (data: DepartmentInput): Promise<DepartmentDetail> => {
    const response = await apiClient.post<DepartmentDetail>('v1/departments', data);
    return response.data;
  },

  update: async (id: number, data: Partial<DepartmentInput> & { is_archived?: boolean }): Promise<DepartmentDetail> => {
    const response = await apiClient.patch<DepartmentDetail>(`v1/departments/${id}`, data);
    return response.data;
  },

  addMember: async (id: number, volunteerId: number): Promise<DepartmentDetail> => {
    const response = await apiClient.post<DepartmentDetail>(`v1/departments/${id}/members`, {
      volunteer_id: volunteerId,
    });
    return response.data;
  },

  removeMember: async (id: number, volunteerId: number): Promise<DepartmentDetail> => {
    const response = await apiClient.delete<DepartmentDetail>(`v1/departments/${id}/members/${volunteerId}`);
    return response.data;
  },

  join: async (id: number): Promise<DepartmentDetail> => {
    const response = await apiClient.post<DepartmentDetail>(`v1/departments/${id}/join`);
    return response.data;
  },

  approveMember: async (id: number, volunteerId: number): Promise<DepartmentDetail> => {
    const response = await apiClient.post<DepartmentDetail>(`v1/departments/${id}/members/${volunteerId}/approve`);
    return response.data;
  },

  leave: async (id: number): Promise<DepartmentDetail> => {
    const response = await apiClient.delete<DepartmentDetail>(`v1/departments/${id}/members/me`);
    return response.data;
  },

  getInventory: async (id: number): Promise<DepartmentInventoryItem[]> => {
    const response = await apiClient.get<DepartmentInventoryItem[]>(`v1/departments/${id}/inventory`);
    return response.data;
  },

  createInventoryItem: async (id: number, data: DepartmentInventoryItemInput): Promise<DepartmentInventoryItem> => {
    const response = await apiClient.post<DepartmentInventoryItem>(`v1/departments/${id}/inventory`, data);
    return response.data;
  },

  updateInventoryItem: async (id: number, itemId: number, data: DepartmentInventoryItemInput): Promise<DepartmentInventoryItem> => {
    const response = await apiClient.put<DepartmentInventoryItem>(`v1/departments/${id}/inventory/${itemId}`, data);
    return response.data;
  },

  deleteInventoryItem: async (id: number, itemId: number): Promise<void> => {
    await apiClient.delete(`v1/departments/${id}/inventory/${itemId}`);
  },
};
