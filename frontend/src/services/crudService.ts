import apiClient from '@/lib/api';
import type { Paginated } from '@/types';

/**
 * Builds a typed CRUD service for a paginated DRF resource.
 *
 * @param path resource path relative to the API base, e.g. "v1/volunteers/".
 */
export function createCrudService<T, TInput>(path: string) {
  return {
    getAll: async (): Promise<T[]> => {
      const response = await apiClient.get<Paginated<T>>(path);
      return response.data.results;
    },

    getById: async (id: number): Promise<T> => {
      const response = await apiClient.get<T>(`${path}${id}/`);
      return response.data;
    },

    create: async (data: TInput): Promise<T> => {
      const response = await apiClient.post<T>(path, data);
      return response.data;
    },

    update: async (id: number, data: Partial<TInput>): Promise<T> => {
      const response = await apiClient.patch<T>(`${path}${id}/`, data);
      return response.data;
    },

    delete: async (id: number): Promise<void> => {
      await apiClient.delete(`${path}${id}/`);
    },
  };
}
