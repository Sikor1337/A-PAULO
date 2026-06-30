import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import ProtectedRoute from './ProtectedRoute';
import { useAuthStore } from '../stores/authStore';
import { permissionService } from '@/services/permissionService';

const renderProtectedRoute = () =>
  render(
    <MemoryRouter initialEntries={['/private']}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/private" element={<h1>Private page</h1>} />
        </Route>
        <Route path="/login" element={<h1>Login page</h1>} />
      </Routes>
    </MemoryRouter>,
  );

describe('ProtectedRoute', () => {
  beforeEach(() => useAuthStore.setState({ user: null, isAuthenticated: false }));
  afterEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false });
    vi.restoreAllMocks();
  });

  it('redirects unauthenticated users to login', () => {
    renderProtectedRoute();

    expect(screen.getByRole('heading', { name: 'Login page' })).toBeInTheDocument();
  });

  it('redirects when a token exists but the user profile is missing', () => {
    useAuthStore.setState({ user: null, isAuthenticated: true });

    renderProtectedRoute();

    expect(screen.getByRole('heading', { name: 'Login page' })).toBeInTheDocument();
  });

  it('renders nested routes for authenticated users', () => {
    useAuthStore.setState({
      user: {
        id: 1,
        email: 'anna@example.org',
        first_name: 'Anna',
        last_name: 'Nowak',
        status: 'admin',
      },
      isAuthenticated: true,
    });

    renderProtectedRoute();

    expect(screen.getByRole('heading', { name: 'Private page' })).toBeInTheDocument();
  });

  it('blocks a route when the inherited permission is missing', async () => {
    useAuthStore.setState({
      user: { id: 1, email: 'anna@example.org', first_name: 'Anna', last_name: 'Nowak', status: 'regular' },
      isAuthenticated: true,
    });
    vi.spyOn(permissionService, 'getMine').mockResolvedValue({ permissions: [], group_ids: [] });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/private']}>
          <Routes>
            <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_USERS" />}>
              <Route path="/private" element={<h1>Private page</h1>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'Brak dostępu' })).toBeInTheDocument();
  });
});
