import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errors';
import { recruitmentService } from '@/services/recruitmentService';
import type {
  OnboardingMeetingType,
  RecruitmentFieldDraft,
  RecruitmentStatus,
  RecruitmentSubmission,
} from '@/types';

export function useRecruitmentForm(accessToken: string) {
  return useQuery({
    queryKey: ['recruitment-form', accessToken],
    queryFn: () => recruitmentService.getForm(accessToken),
    retry: false,
  });
}

export function useRecruitmentAccessLink() {
  return useQuery({
    queryKey: ['recruitment-access-link'],
    queryFn: recruitmentService.getAccessLink,
  });
}

export function useRecruitmentFields() {
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ['recruitment-fields'], queryFn: recruitmentService.getFields });
  const save = useMutation({
    mutationFn: (fields: RecruitmentFieldDraft[]) => recruitmentService.saveFields(fields),
    onSuccess: (fields) => {
      queryClient.setQueryData(['recruitment-fields'], fields);
      queryClient.invalidateQueries({ queryKey: ['recruitment-form'] });
    },
    onError: (error) => alert(parseApiError(error, 'Nie udało się zapisać formularza.')),
  });
  return { data: list.data, isLoading: list.isLoading, save };
}

export function useRecruitmentSubmissions(status?: RecruitmentStatus) {
  const queryClient = useQueryClient();
  const list = useQuery({
    queryKey: ['recruitment-submissions', status ?? 'all'],
    queryFn: () => recruitmentService.getSubmissions(status),
  });
  const action = useMutation({
    mutationFn: ({
      id,
      action: nextAction,
      note,
    }: {
      id: number;
      action: 'start-onboarding' | 'return' | 'accept' | 'reject' | 'restore-onboarding';
      note?: string;
    }) => recruitmentService.transition(id, nextAction, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitment-submissions'] });
      queryClient.invalidateQueries({ queryKey: ['volunteers'] });
    },
    onError: (error) => alert(parseApiError(error, 'Nie udało się zmienić etapu rekrutacji.')),
  });
  const meeting = useMutation({
    mutationFn: ({
      id,
      meetingType,
      attended,
    }: {
      id: number;
      meetingType: OnboardingMeetingType;
      attended: boolean;
    }) => recruitmentService.setOnboardingAttendance(id, meetingType, attended),
    onSuccess: (updated) => {
      queryClient.setQueriesData<RecruitmentSubmission[]>(
        { queryKey: ['recruitment-submissions'] },
        (current) => Array.isArray(current)
          ? current.map((item) => (
            item.id === updated.id ? updated : item
          ))
          : current,
      );
    },
    onError: (error) => alert(parseApiError(error, 'Nie udało się zapisać obecności.')),
  });
  return { data: list.data, isLoading: list.isLoading, action, meeting };
}
