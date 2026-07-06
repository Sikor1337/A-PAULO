import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import EventFormModal from './EventFormModal';

vi.mock('@/hooks/useUnsavedChanges', () => ({
  useUnsavedChanges: () => () => true,
}));

describe('EventFormModal', () => {
  it('sets both dates to the clicked day for an all-day event', async () => {
    render(
      <EventFormModal
        event={null}
        initialDate={new Date(2026, 6, 10, 14, 30)}
        isPending={false}
        onClose={vi.fn()}
        onSave={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByLabelText('Cały dzień'));

    await waitFor(() => {
      expect(screen.getByLabelText('Początek')).toHaveValue('2026-07-10');
      expect(screen.getByLabelText('Koniec')).toHaveValue('2026-07-10');
    });
  });

  it('adds an end date to a recurrence rule', async () => {
    const onSave = vi.fn();
    render(
      <EventFormModal
        event={null}
        initialDate={new Date(2026, 6, 10, 14, 30)}
        isPending={false}
        onClose={vi.fn()}
        onSave={onSave}
      />,
    );

    fireEvent.change(screen.getByLabelText('Tytuł'), { target: { value: 'Dyżur' } });
    fireEvent.change(screen.getByLabelText('Powtarzanie'), { target: { value: 'FREQ=DAILY' } });
    fireEvent.change(screen.getByLabelText('Powtarzaj do'), { target: { value: '2026-07-31' } });
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz' }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
        recurrence_rule: 'FREQ=DAILY;UNTIL=20260731T235959Z',
      }));
    });
  });
});
