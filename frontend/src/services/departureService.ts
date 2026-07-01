import apiClient from '@/lib/api';
import type {
  DepartureField,
  DepartureFieldDraft,
  DepartureInterview,
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

  create: async (
    volunteerId: number,
    answers: Record<string, unknown>,
  ): Promise<DepartureInterview> => {
    const response = await apiClient.post<DepartureInterview>(path, {
      volunteer_id: volunteerId,
      answers,
    });
    return response.data;
  },
};
