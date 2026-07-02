import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it } from 'vitest';
import EventsPage from './EventsPage';

describe('EventsPage', () => {
  it('embeds the PaP Google Calendar', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/events']}>
          <EventsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Wydarzenia' })).toBeInTheDocument();
    expect(screen.getByTitle('Kalendarz wydarzeń PaP')).toHaveAttribute(
      'src',
      'https://calendar.google.com/calendar/embed?src=projektapaulo%40gmail.com&ctz=Europe%2FWarsaw',
    );
  });
});
