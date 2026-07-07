import apiClient from '@/lib/api';
import type { Task, TaskCreateInput, TaskFilters, TaskUpdateInput } from '@/types';

export const taskService = {
  list: async (filters: Partial<TaskFilters> = {}): Promise<Task[]> => {
    const params: Record<string, string | number> = {};
    if (filters.departmentId) params.department_id = filters.departmentId;
    if (filters.eventId) params.event_id = filters.eventId;
    if (filters.status) params.status = filters.status;
    if (filters.volunteerId) params.volunteer_id = filters.volunteerId;
    const response = await apiClient.get<Task[]>('v1/tasks', { params });
    return response.data;
  },

  create: async (data: TaskCreateInput): Promise<Task> => {
    const response = await apiClient.post<Task>('v1/tasks', data);
    return response.data;
  },

  update: async (id: number, data: TaskUpdateInput): Promise<Task> => {
    const response = await apiClient.patch<Task>(`v1/tasks/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`v1/tasks/${id}`);
  },

  addChecklistItem: async (taskId: number, label: string): Promise<Task> => {
    const response = await apiClient.post<Task>(`v1/tasks/${taskId}/checklist`, { label });
    return response.data;
  },

  updateChecklistItem: async (
    taskId: number,
    itemId: number,
    data: { label?: string; is_done?: boolean },
  ): Promise<Task> => {
    const response = await apiClient.patch<Task>(`v1/tasks/${taskId}/checklist/${itemId}`, data);
    return response.data;
  },

  deleteChecklistItem: async (taskId: number, itemId: number): Promise<Task> => {
    const response = await apiClient.delete<Task>(`v1/tasks/${taskId}/checklist/${itemId}`);
    return response.data;
  },
};
