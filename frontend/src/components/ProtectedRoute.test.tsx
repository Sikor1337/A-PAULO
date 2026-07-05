import { fireEvent, render, screen } from '@testing-library/react';
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
  beforeEach(() => {
    sessionStorage.clear();
    useAuthStore.setState({ user: null, isAuthenticated: false });
  });
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

  it('sends a recruitment account away from operational routes', async () => {
    useAuthStore.setState({
      user: {
        id: 2,
        email: 'candidate@example.org',
        first_name: 'Anna',
        last_name: 'Kandydatka',
        status: 'new_volunteer',
      },
      isAuthenticated: true,
    });

    render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route element={<ProtectedRoute allowedStatuses={['regular', 'admin']} />}>
            <Route path="/private" element={<h1>Private page</h1>} />
          </Route>
          <Route path="/recruitment-required" element={<h1>Recruitment required</h1>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: 'Recruitment required' })).toBeInTheDocument();
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
            <Route path="/login" element={<h1>Login page</h1>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'Brak dostępu' })).toBeInTheDocument();
    expect(screen.getByText('To konto nie ma uprawnienia wymaganego do tej sekcji.')).toBeVisible();
  });

  it('lets a blocked user log out and change account', async () => {
    localStorage.setItem('access_token', 'access');
    localStorage.setItem('refresh_token', 'refresh');
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
            <Route path="/login" element={<h1>Login page</h1>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(await screen.findByRole('button', { name: 'Wyloguj i zmień konto' }));

    expect(await screen.findByRole('heading', { name: 'Login page' })).toBeInTheDocument();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
