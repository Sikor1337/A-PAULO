import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/stores/authStore';
import RegisterPage from './RegisterPage';

vi.mock('@/services/authService', () => ({
  authService: { register: vi.fn() },
}));

const token = 'a'.repeat(64);

const renderPage = (path: string) => render(
  <MemoryRouter initialEntries={[path]}>
    <Routes>
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<h1>Login</h1>} />
    </Routes>
  </MemoryRouter>,
);

const submitForm = () => {
  fireEvent.change(screen.getByLabelText('Nazwa użytkownika'), { target: { value: 'nowy-user' } });
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'nowy@example.com' } });
  fireEvent.change(screen.getByLabelText('Hasło'), { target: { value: 'StrongPass123' } });
  fireEvent.change(screen.getByLabelText('Potwierdź hasło'), { target: { value: 'StrongPass123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Utwórz konto' }));
};

describe('RegisterPage', () => {
  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem('recruitment_access_token', token);
    useAuthStore.setState({ user: null, isAuthenticated: false });
    vi.mocked(authService.register).mockResolvedValue({
      id: 2,
      username: 'nowy-user',
      email: 'nowy@example.com',
      first_name: '',
      last_name: '',
      status: 'regular',
    });
  });

  it('does not attach a stale recruitment token to normal registration', async () => {
    renderPage('/register');
    submitForm();

    await waitFor(() => expect(authService.register).toHaveBeenCalledWith(
      expect.objectContaining({ recruitment_token: undefined }),
    ));
  });

  it('attaches the token only in the explicit recruitment flow', async () => {
    renderPage('/register?recruitment=1');
    submitForm();

    await waitFor(() => expect(authService.register).toHaveBeenCalledWith(
      expect.objectContaining({ recruitment_token: token }),
    ));
  });
});
