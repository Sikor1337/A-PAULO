import axiosClient from '@/lib/api';
import type { AuditEvent } from '@/types';

export const auditService = {
  async listHistory(path: string): Promise<AuditEvent[]> {
    const response = await axiosClient.get<AuditEvent[]>(path);
    return response.data;
  },
};
