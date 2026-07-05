import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { departureService } from '@/services/departureService';
import type { DepartureFieldDraft, DepartureSelfService } from '@/types';

export const useDepartureFields = (enabled = true) => {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['departure-fields'],
    queryFn: departureService.getFields,
    enabled,
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

export const useMyDepartureSurvey = (enabled = true) => {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['my-departure-survey'],
    queryFn: departureService.getMine,
    retry: false,
    enabled,
  });
  const save = useMutation({
    mutationFn: (answers: Record<string, unknown>) => (
      query.data?.interview
        ? departureService.updateMine(answers)
        : departureService.submitMine(answers)
    ),
    onSuccess: (interview) => {
      queryClient.setQueryData<DepartureSelfService>(
        ['my-departure-survey'],
        (current) => current ? { ...current, interview } : current,
      );
      queryClient.invalidateQueries({ queryKey: ['volunteers'] });
      queryClient.invalidateQueries({ queryKey: ['departure-interviews'] });
    },
  });
  return { ...query, save };
};
