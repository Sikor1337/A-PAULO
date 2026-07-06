import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import RecruitmentLayout from './RecruitmentLayout';

vi.mock('@/components/layout/PageShell', () => ({
  default: ({ children }: { children: React.ReactNode }) => <main>{children}</main>,
}));

describe('RecruitmentLayout', () => {
  it('separates surveys, survey kinds and editor/response views', () => {
    render(
      <MemoryRouter initialEntries={['/recruitment/surveys/recruitment/editor']}>
        <Routes>
          <Route path="/recruitment" element={<RecruitmentLayout />}>
            <Route path="surveys/recruitment/editor" element={<p>Treść edytora</p>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: 'Ankiety' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Wdrażanie' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Rekrutacja' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ankieta odejścia' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Edycja' })).toHaveAttribute(
      'href',
      '/recruitment/surveys/recruitment/editor',
    );
    expect(screen.getByRole('link', { name: 'Odpowiedzi' })).toHaveAttribute(
      'href',
      '/recruitment/surveys/recruitment/responses',
    );
  });
});
