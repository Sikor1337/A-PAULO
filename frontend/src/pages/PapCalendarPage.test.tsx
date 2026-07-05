import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import PapCalendarPage, { PAP_GOOGLE_CALENDAR_URL } from './PapCalendarPage';

vi.mock('@/components/layout/PageShell', () => ({
  default: ({ children }: { children: React.ReactNode }) => <main>{children}</main>,
}));

describe('PapCalendarPage', () => {
  it('embeds the public PaP Google Calendar', () => {
    render(<PapCalendarPage />);

    expect(screen.getByRole('heading', { name: 'Kalendarz PAP' })).toBeInTheDocument();
    expect(screen.getByTitle('Kalendarz PAP')).toHaveAttribute('src', PAP_GOOGLE_CALENDAR_URL);
    expect(screen.getByTitle('Kalendarz PAP')).toHaveAttribute('referrerPolicy', 'no-referrer');
  });
});
