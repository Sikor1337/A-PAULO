import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';
import { useAuthStore } from '@/stores/authStore';
import RecruitmentEntryPage from './RecruitmentEntryPage';

const token = 'b'.repeat(64);

const renderEntry = () => render(
  <MemoryRouter initialEntries={[`/recrutation/${token}`]}>
    <Routes>
      <Route path="/recrutation/:token" element={<RecruitmentEntryPage />} />
      <Route path="/login" element={<h1>Login page</h1>} />
      <Route path="/dashboard" element={<h1>Dashboard page</h1>} />
    </Routes>
  </MemoryRouter>,
);

describe('RecruitmentEntryPage', () => {
  beforeEach(() => {
    sessionStorage.clear();
    useAuthStore.setState({ user: null, isAuthenticated: false });
  });

  it('preserves the invite and sends a guest to login', async () => {
    renderEntry();

    expect(await screen.findByRole('heading', { name: 'Login page' })).toBeInTheDocument();
    expect(sessionStorage.getItem('recruitment_access_token')).toBe(token);
  });

  it('does not force a regular account into the survey', async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      user: {
        id: 3,
        email: 'user@example.com',
        first_name: 'Regular',
        last_name: 'User',
        status: 'regular',
      },
    });

    renderEntry();

    expect(await screen.findByRole('heading', { name: 'Dashboard page' })).toBeInTheDocument();
    expect(sessionStorage.getItem('recruitment_access_token')).toBeNull();
  });
});
