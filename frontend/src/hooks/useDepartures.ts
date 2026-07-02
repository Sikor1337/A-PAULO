import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { departureService } from '@/services/departureService';
import type { DepartureFieldDraft } from '@/types';

export const useDepartureFields = () => {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['departure-fields'],
    queryFn: departureService.getFields,
  });
  const save = useMutation({
    mutationFn: (fields: DepartureFieldDraft[]) => departureService.saveFields(fields),
    onSuccess: (fields) => {
      queryClient.setQueryData(['departure-fields'], fields);
    },
  });
  return { ...query, save };
};

export const useDepartureInterviews = () => useQuery({
  queryKey: ['departure-interviews'],
  queryFn: departureService.getAll,
});

export const useCreateDepartureInterview = (onSuccess?: () => void) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      volunteerId,
      answers,
    }: {
      volunteerId: number;
      answers: Record<string, unknown>;
    }) => departureService.create(volunteerId, answers),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers'] });
      queryClient.invalidateQueries({ queryKey: ['departure-interviews'] });
      onSuccess?.();
    },
  });
};
