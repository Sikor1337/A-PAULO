import apiClient from '../lib/api';

export const groupService = {
    getAll: async () => {
        const response = await apiClient.get('v1/groups');
        return response.data;
    },

    getById: async (id: number) => {
        const response = await apiClient.get(`v1/groups/${id}`);
        return response.data;
    },

    create: async (data: any) => {
        const response = await apiClient.post('v1/groups', data);
        return response.data;
    },

    update: async (id: number, data: any) => {
        const response = await apiClient.patch(`v1/groups/${id}`, data);
        return response.data;
    },

    delete: async (id: number) => {
        await apiClient.delete(`v1/groups/${id}`);
    },

    // Assignments
    getAssignments: async () => {
        const response = await apiClient.get('v1/groups/assignments');
        return response.data;
    },

    createAssignment: async (data: { beneficiary: number; volunteer: number }) => {
        const response = await apiClient.post('v1/groups/assignments', data);
        return response.data;
    },

    deleteAssignment: async (id: number) => {
        await apiClient.delete(`v1/groups/assignments/${id}`);
    },
};
