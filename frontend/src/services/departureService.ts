import apiClient from '@/lib/api';
import type {
  DepartureField,
  DepartureFieldDraft,
  DepartureInterview,
  DepartureSelfService,
} from '@/types';

const path = 'v1/recruitment/departures';

export const departureService = {
  getFields: async (): Promise<DepartureField[]> => {
    const response = await apiClient.get<DepartureField[]>(`${path}/fields`);
    return response.data;
  },

  saveFields: async (fields: DepartureFieldDraft[]): Promise<DepartureField[]> => {
    const response = await apiClient.put<DepartureField[]>(`${path}/fields`, { fields });
    return response.data;
  },

  getAll: async (): Promise<DepartureInterview[]> => {
    const response = await apiClient.get<DepartureInterview[]>(path, {
      params: { skip: 0, limit: 1000 },
    });
    return response.data;
  },

  getMine: async (): Promise<DepartureSelfService> => {
    const response = await apiClient.get<DepartureSelfService>(`${path}/me`);
    return response.data;
  },

  submitMine: async (answers: Record<string, unknown>): Promise<DepartureInterview> => {
    const response = await apiClient.post<DepartureInterview>(`${path}/me`, { answers });
    return response.data;
  },

  updateMine: async (answers: Record<string, unknown>): Promise<DepartureInterview> => {
    const response = await apiClient.put<DepartureInterview>(`${path}/me`, { answers });
    return response.data;
  },
};
