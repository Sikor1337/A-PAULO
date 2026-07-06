import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import SurveyResponses from './SurveyResponses';

const records = [{
  id: 1,
  title: 'Anna Kowalska',
  subtitle: 'Wysłano dzisiaj',
  summary: 'anna@example.com',
  source: { kind: 'recruitment' },
  answers: [{ key: 'reason', label: 'Dlaczego?', value: 'Chcę pomagać' }],
}];

describe('SurveyResponses', () => {
  it('provides the same searchable list and answer preview for every survey', () => {
    render(
      <SurveyResponses
        title="Odpowiedzi"
        description="Opis"
        records={records}
        isLoading={false}
        emptyText="Brak"
      />,
    );

    fireEvent.change(screen.getByPlaceholderText('Szukaj osoby…'), { target: { value: 'Anna' } });
    fireEvent.click(screen.getByRole('button', { name: /Anna Kowalska/ }));
    expect(screen.getByText('Chcę pomagać')).toBeInTheDocument();
  });
});
