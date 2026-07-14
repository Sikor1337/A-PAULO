import { useQuery } from '@tanstack/react-query';
import { auditService } from '@/services/auditService';

export const useAuditHistory = (path: string, enabled: boolean) =>
  useQuery({
    queryKey: ['audit-history', path],
    queryFn: () => auditService.listHistory(path),
    enabled,
  });
