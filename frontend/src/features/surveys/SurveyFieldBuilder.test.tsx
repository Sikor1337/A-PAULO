import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import SurveyFieldBuilder from './SurveyFieldBuilder';

vi.mock('@/hooks/useUnsavedChanges', () => ({
  useUnsavedChanges: () => async () => true,
}));

const field = {
  id: 1,
  label: 'Dlaczego?',
  field_type: 'textarea' as const,
  required: true,
  placeholder: '',
  options: [],
  is_active: true,
  is_system: false,
};

describe('SurveyFieldBuilder', () => {
  it('shows readable field type and status badges', () => {
    render(
      <SurveyFieldBuilder
        title="Pytania"
        description="Opis"
        fields={[{ ...field, is_system: true }]}
        isLoading={false}
        isSaving={false}
        canManage
        onSave={vi.fn()}
      />,
    );

    expect(screen.getByText('Długa odpowiedź')).toBeInTheDocument();
    expect(screen.getByText('Wymagane')).toBeInTheDocument();
    expect(screen.getByText('Podstawowe')).toBeInTheDocument();
    expect(screen.queryByText(/textarea · wymagane/i)).not.toBeInTheDocument();
  });

  it('uses one edit-and-save flow for every survey definition', () => {
    const onSave = vi.fn((_fields, onSuccess: () => void) => onSuccess());
    render(
      <SurveyFieldBuilder
        title="Pytania"
        description="Opis"
        fields={[field]}
        isLoading={false}
        isSaving={false}
        canManage
        onSave={onSave}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Edytuj formularz' }));
    fireEvent.click(screen.getByRole('button', { name: 'Edytuj' }));
    fireEvent.change(screen.getByLabelText('Treść pytania'), { target: { value: 'Nowe pytanie' } });
    fireEvent.click(screen.getByRole('button', { name: 'Zastosuj zmianę' }));
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz formularz' }));

    expect(onSave).toHaveBeenCalledWith(
      [expect.objectContaining({ label: 'Nowe pytanie' })],
      expect.any(Function),
    );
  });
});
