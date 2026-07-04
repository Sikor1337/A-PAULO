import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useMyDepartureSurvey } from '@/hooks/useDepartures';
import MyDepartureSurveyPage from './MyDepartureSurveyPage';

vi.mock('@/components/layout/PageShell', () => ({
  default: ({ children }: { children: React.ReactNode }) => <main>{children}</main>,
}));
vi.mock('@/hooks/useDepartures', () => ({
  useMyDepartureSurvey: vi.fn(),
}));

const field = {
  id: 1,
  key: 'departure_reason',
  label: 'Dlaczego odchodzisz?',
  field_type: 'textarea' as const,
  required: true,
  placeholder: '',
  options: [],
  position: 0,
  is_active: true,
  is_system: true,
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:00:00Z',
};

const mockSurvey = (interview: object | null = null) => {
  const mutate = vi.fn();
  vi.mocked(useMyDepartureSurvey).mockReturnValue({
    data: {
      volunteer: { id: 4, full_name: 'Jan Kowalski', email: 'jan@example.com' },
      fields: [field],
      interview,
    },
    isLoading: false,
    isError: false,
    error: null,
    submit: { mutate, isPending: false, isError: false, error: null },
  } as unknown as ReturnType<typeof useMyDepartureSurvey>);
  return mutate;
};

describe('MyDepartureSurveyPage', () => {
  it('lets the volunteer submit their own answers', () => {
    const mutate = mockSurvey();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<MyDepartureSurveyPage />);

    expect(screen.getByText('Jan Kowalski')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Dlaczego odchodzisz/), {
      target: { value: 'Zmiana planów' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Wyślij ankietę' }));

    expect(mutate).toHaveBeenCalledWith(expect.objectContaining({
      departure_reason: 'Zmiana planów',
    }));
  });

  it('does not allow a submitted interview to be filled again', () => {
    mockSurvey({ departure_date: '2026-07-01' });
    render(<MyDepartureSurveyPage />);

    expect(screen.getByText('Ankieta została wysłana')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Wyślij ankietę' })).not.toBeInTheDocument();
  });
});
