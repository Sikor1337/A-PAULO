import apiClient from '@/lib/api';
import type {
  CalendarEvent,
  CalendarEventInput,
  CalendarFilters,
  FeedTokenCreated,
  FeedTokenStatus,
} from '@/types';

const eventsPath = 'v1/calendar/events';
const tokenPath = 'v1/calendar/feed-token';

export const calendarService = {
  getEvents: async (filters: CalendarFilters = {}): Promise<CalendarEvent[]> => {
    const response = await apiClient.get<CalendarEvent[]>(eventsPath, {
      params: {
        starts_from: filters.startsFrom,
        starts_to: filters.startsTo,
        status: filters.status || undefined,
        visibility: filters.visibility || undefined,
        sort: filters.sort ?? 'asc',
        limit: 1000,
      },
    });
    return response.data;
  },
  createEvent: async (input: CalendarEventInput): Promise<CalendarEvent> => {
    const response = await apiClient.post<CalendarEvent>(eventsPath, input);
    return response.data;
  },
  updateEvent: async (id: number, input: Partial<CalendarEventInput>): Promise<CalendarEvent> => {
    const response = await apiClient.patch<CalendarEvent>(`${eventsPath}/${id}`, input);
    return response.data;
  },
  cancelEvent: async (id: number): Promise<CalendarEvent> => {
    const response = await apiClient.post<CalendarEvent>(`${eventsPath}/${id}/cancel`);
    return response.data;
  },
  deleteEvent: async (id: number): Promise<void> => {
    await apiClient.delete(`${eventsPath}/${id}`);
  },
  downloadEvent: async (event: CalendarEvent): Promise<void> => {
    const response = await apiClient.get<Blob>(`${eventsPath}/${event.id}.ics`, { responseType: 'blob' });
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `wydarzenie-${event.id}.ics`;
    link.click();
    URL.revokeObjectURL(url);
  },
  getFeedTokenStatus: async (): Promise<FeedTokenStatus> => {
    const response = await apiClient.get<FeedTokenStatus>(tokenPath);
    return response.data;
  },
  generateFeedToken: async (): Promise<FeedTokenCreated> => {
    const response = await apiClient.post<FeedTokenCreated>(tokenPath);
    return response.data;
  },
  revokeFeedToken: async (): Promise<void> => {
    await apiClient.delete(tokenPath);
  },
};
