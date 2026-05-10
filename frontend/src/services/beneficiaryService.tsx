import apiClient from '../lib/api';

export const beneficiaryService = {
  getAll: async () => {
    const response = await apiClient.get('v1/beneficiaries/');
    return response.data.results;
  },

  create: async (data: any) => {
    const response = await apiClient.post('v1/beneficiaries/', data);
    return response.data;
  },

  update: async (id: number, data: any) => {
    const response = await apiClient.patch(`v1/beneficiaries/${id}/`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`v1/beneficiaries/${id}/`);
  }
};
