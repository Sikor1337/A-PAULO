import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parseApiError } from '@/lib/errors';
import { appDialog } from '@/lib/appDialog';
import { calendarService } from '@/services/calendarService';
import type { CalendarEvent, CalendarEventInput, CalendarFilters } from '@/types';

export function useCalendarEvents(filters: CalendarFilters) {
  const queryClient = useQueryClient();
  const events = useQuery({
    queryKey: ['calendar-events', filters],
    queryFn: () => calendarService.getEvents(filters),
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
  const onError = (error: unknown) => appDialog.error(parseApiError(error, 'Nie udało się zapisać wydarzenia.'));
  const save = useMutation({
    mutationFn: ({ event, input }: { event: CalendarEvent | null; input: CalendarEventInput }) =>
      event ? calendarService.updateEvent(event.id, input) : calendarService.createEvent(input),
    onSuccess: refresh,
    onError,
  });
  const cancel = useMutation({ mutationFn: calendarService.cancelEvent, onSuccess: refresh, onError });
  const remove = useMutation({ mutationFn: calendarService.deleteEvent, onSuccess: refresh, onError });
  return { ...events, save, cancel, remove };
}

export function useCalendarSubscription() {
  const queryClient = useQueryClient();
  const onError = (error: unknown) => appDialog.error(parseApiError(error, 'Nie udało się zmienić subskrypcji kalendarza.'));
  const status = useQuery({
    queryKey: ['calendar-feed-token'],
    queryFn: calendarService.getFeedTokenStatus,
  });
  const generate = useMutation({
    mutationFn: calendarService.generateFeedToken,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['calendar-feed-token'] }),
    onError,
  });
  const revoke = useMutation({
    mutationFn: calendarService.revokeFeedToken,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['calendar-feed-token'] }),
    onError,
  });
  return { status, generate, revoke };
}
