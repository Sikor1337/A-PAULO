import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errors';
import { recruitmentService } from '@/services/recruitmentService';
import type { RecruitmentFieldInput, RecruitmentInvitationInput, RecruitmentStatus } from '@/types';

export function useRecruitmentForm(token?: string) {
  return useQuery({
    queryKey: ['recruitment-form', token],
    queryFn: () => recruitmentService.getInvitedForm(token!),
    enabled: Boolean(token),
    retry: false,
  });
}

export function useRecruitmentFields() {
  const queryClient = useQueryClient();
  const list = useQuery({ queryKey: ['recruitment-fields'], queryFn: recruitmentService.getFields });
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['recruitment-fields'] });
    queryClient.invalidateQueries({ queryKey: ['recruitment-form'] });
  };
  const create = useMutation({
    mutationFn: recruitmentService.createField,
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error, 'Nie udało się dodać pytania.')),
  });
  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<RecruitmentFieldInput> }) =>
      recruitmentService.updateField(id, data),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error, 'Nie udało się zmienić pytania.')),
  });
  const remove = useMutation({
    mutationFn: recruitmentService.deleteField,
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error, 'Nie udało się usunąć pytania.')),
  });
  const reorder = useMutation({
    mutationFn: recruitmentService.reorderFields,
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error, 'Nie udało się zmienić kolejności pytań.')),
  });
  return { data: list.data, isLoading: list.isLoading, create, update, remove, reorder };
}

export function useRecruitmentInvitations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['recruitment-invitations'] });
  const list = useQuery({ queryKey: ['recruitment-invitations'], queryFn: recruitmentService.getInvitations });
  const create = useMutation({
    mutationFn: (data: RecruitmentInvitationInput) => recruitmentService.createInvitation(data),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error, 'Nie udało się utworzyć zaproszenia.')),
  });
  const revoke = useMutation({
    mutationFn: recruitmentService.revokeInvitation,
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error, 'Nie udało się wyłączyć zaproszenia.')),
  });
  return { data: list.data, isLoading: list.isLoading, create, revoke };
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
      reason,
    }: {
      id: number;
      action: 'start-onboarding' | 'return' | 'accept' | 'reject';
      reason?: string;
    }) => recruitmentService.transition(id, nextAction, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitment-submissions'] });
      queryClient.invalidateQueries({ queryKey: ['volunteers'] });
    },
    onError: (error) => alert(parseApiError(error, 'Nie udało się zmienić etapu rekrutacji.')),
  });
  return { data: list.data, isLoading: list.isLoading, action };
}
