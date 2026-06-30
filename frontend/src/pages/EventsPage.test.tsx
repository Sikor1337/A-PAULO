import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { calendarService } from '@/services/calendarService';
import EventsPage from './EventsPage';

describe('EventsPage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('renders events from A-PAULO in the organization month calendar', async () => {
    const now = new Date();
    vi.spyOn(calendarService, 'getEvents').mockResolvedValue([{
      id: 1,
      uid: 'event-1@a-paulo',
      title: 'Spotkanie organizacyjne',
      description: '',
      starts_at: now.toISOString(),
      ends_at: new Date(now.getTime() + 60 * 60_000).toISOString(),
      timezone: 'Europe/Warsaw',
      is_all_day: false,
      location: 'Biuro',
      recurrence_rule: null,
      status: 'published',
      visibility: 'organization',
      author_id: 1,
      author_name: 'Anna Nowak',
      sequence: 0,
      created_at: now.toISOString(),
      updated_at: now.toISOString(),
    }]);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/events']}>
          <EventsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Wydarzenia' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Subskrybuj .ics' })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /Spotkanie organizacyjne/ })).toBeInTheDocument();
  });
});
