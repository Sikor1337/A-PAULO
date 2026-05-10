import apiClient from '../lib/api';

export const volunteerService = {
    getAll: async () => {
        const response = await apiClient.get('v1/volunteers/');
        return response.data.results;
    },

    create: async (data: any) => {
        const response = await apiClient.post('v1/volunteers/', data);
        return response.data;
    },

    update: async (id: number, data: any) => {
        const response = await apiClient.patch(`v1/volunteers/${id}/`, data);
        return response.data;
    },

    delete: async (id: number) => {
        await apiClient.delete(`v1/volunteers/${id}/`);
    }
};
