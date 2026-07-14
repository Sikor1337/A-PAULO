import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { appDialog } from '@/lib/appDialog';
import { parseApiError } from '@/lib/errors';
import { beneficiaryRecruitmentService } from '@/services/beneficiaryRecruitmentService';
import type { RecruitmentFieldDraft } from '@/types';

export const usePublicBeneficiaryRecruitmentForm = (token: string) => useQuery({
  queryKey: ['beneficiary-recruitment-form', token],
  queryFn: () => beneficiaryRecruitmentService.getForm(token),
  retry: false,
});

export const useBeneficiaryRecruitmentFields = () => {
  const client = useQueryClient();
  const fields = useQuery({ queryKey: ['beneficiary-recruitment-fields'], queryFn: beneficiaryRecruitmentService.getFields });
  const save = useMutation({
    mutationFn: (draft: RecruitmentFieldDraft[]) => beneficiaryRecruitmentService.saveFields(draft),
    onSuccess: (data) => client.setQueryData(['beneficiary-recruitment-fields'], data),
    onError: (error) => appDialog.error(parseApiError(error)),
  });
  return { ...fields, save };
};

export const useBeneficiaryRecruitmentAccessLink = () => useQuery({
  queryKey: ['beneficiary-recruitment-access-link'],
  queryFn: beneficiaryRecruitmentService.getAccessLink,
});

export const useBeneficiaryRecruitmentSubmissions = (includeArchived: boolean) => {
  const client = useQueryClient();
  const list = useQuery({
    queryKey: ['beneficiary-recruitment-submissions', includeArchived],
    queryFn: () => beneficiaryRecruitmentService.getSubmissions(includeArchived),
  });
  const refresh = () => {
    client.invalidateQueries({ queryKey: ['beneficiary-recruitment-submissions'] });
    client.invalidateQueries({ queryKey: ['beneficiaries'] });
  };
  const onError = (error: unknown) => appDialog.error(parseApiError(error));
  const createBeneficiary = useMutation({ mutationFn: beneficiaryRecruitmentService.createBeneficiary, onSuccess: refresh, onError });
  const reject = useMutation({ mutationFn: ({ id, comment }: { id: number; comment: string | null }) => beneficiaryRecruitmentService.reject(id, comment), onSuccess: refresh, onError });
  const archive = useMutation({ mutationFn: beneficiaryRecruitmentService.archive, onSuccess: refresh, onError });
  const remove = useMutation({ mutationFn: beneficiaryRecruitmentService.remove, onSuccess: refresh, onError });
  return { ...list, createBeneficiary, reject, archive, remove };
};
