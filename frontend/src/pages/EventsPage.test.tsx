import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import EventsPage from './EventsPage';

describe('EventsPage', () => {
  it('embeds the PaP Google Calendar', () => {
    render(
      <MemoryRouter initialEntries={['/events']}>
        <EventsPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Wydarzenia' })).toBeInTheDocument();
    expect(screen.getByTitle('Kalendarz wydarzeń PaP')).toHaveAttribute(
      'src',
      'https://calendar.google.com/calendar/embed?src=projektapaulo%40gmail.com&ctz=Europe%2FWarsaw',
    );
  });
});
