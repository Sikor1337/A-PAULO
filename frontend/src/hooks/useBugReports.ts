import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { bugReportService } from '@/services/bugReportService';
import { parseApiError } from '@/lib/errors';
import type { BugReportSubmitInput, BugReportUpdateInput } from '@/types';

/** All reports (developer view), optionally filtered by status. */
export function useBugReportList(status: string, enabled: boolean) {
  return useQuery({
    queryKey: ['bug-reports', { status }],
    queryFn: () => bugReportService.list(status || undefined),
    enabled,
  });
}

/** The current user's own reports. */
export function useMyBugReports() {
  return useQuery({
    queryKey: ['bug-reports-mine'],
    queryFn: bugReportService.listMine,
  });
}

/** Submit a report / update its status. */
export function useBugReportActions(options?: { onSubmitted?: () => void }) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['bug-reports'] });
    queryClient.invalidateQueries({ queryKey: ['bug-reports-mine'] });
  };

  const submit = useMutation({
    mutationFn: (data: BugReportSubmitInput) => bugReportService.submit(data),
    onSuccess: () => {
      invalidate();
      options?.onSubmitted?.();
    },
    onError: (error) => alert(parseApiError(error)),
  });

  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: BugReportUpdateInput }) =>
      bugReportService.update(id, data),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => bugReportService.remove(id),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  return { submit, update, remove };
}
