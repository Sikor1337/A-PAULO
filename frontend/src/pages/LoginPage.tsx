import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { AxiosError } from 'axios';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/authService';
import { markSessionChanged } from '../lib/sessionLifecycle';
import {
  clearRecruitmentAccessToken,
  destinationForUser,
} from '../lib/recruitmentAccess';

interface LoginFormData {
  email: string;
  password: string;
}

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, user: currentUser } = useAuthStore();
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>();

  // Przekieruj jeśli już zalogowany
  useEffect(() => {
    if (isAuthenticated && currentUser) {
      if (currentUser.status !== 'new_volunteer') clearRecruitmentAccessToken();
      navigate(destinationForUser(currentUser.status));
    }
  }, [currentUser, isAuthenticated, navigate]);

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');

    try {
      // Pobierz tokeny z backendu
      const { access, refresh } = await authService.login(data);

      // Zapisz tymczasowo tokeny aby pobrać profil
      markSessionChanged();
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Get user profile
      try {
        const userProfile = await authService.getUserProfile();
        
        // Map backend user to frontend user format
        const user = {
          id: userProfile.id,
          email: userProfile.email,
          first_name: userProfile.first_name || '',
          last_name: userProfile.last_name || '',
          status: userProfile.status,
        };

        // Update store with user data
        login(access, refresh, user);
        if (user.status !== 'new_volunteer') clearRecruitmentAccessToken();
        navigate(destinationForUser(user.status));
      } catch (profileError) {
        // Clear tokens if profile fetch fails
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        throw profileError;
      }

    } catch (err) {
      console.error('Login error:', err);
      const axiosErr = err as AxiosError<{ detail?: string }>;
      if (axiosErr.response?.status === 401) {
        setError('Nieprawidłowy email lub hasło');
      } else if (axiosErr.response?.data?.detail) {
        setError(axiosErr.response.data.detail);
      } else {
        setError('Wystąpił błąd podczas logowania. Spróbuj ponownie.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-100 px-4 py-6">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-md sm:p-8">
        <h1 className="text-2xl font-bold text-center mb-6 text-gray-900">A-PAULO</h1>
        <h2 className="text-xl text-center mb-6 text-gray-600">Logowanie</h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              {...register('email', {
                required: 'Email jest wymagany',
                pattern: {
                  value: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/,
                  message: 'Nieprawidłowy adres email',
                },
              })}
              className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="twoj@email.pl"
              disabled={isLoading}
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Hasło
            </label>
            <input
              id="password"
              type="password"
              {...register('password', {
                required: 'Hasło jest wymagane',
                minLength: {
                  value: 6,
                  message: 'Hasło musi mieć minimum 6 znaków',
                },
              })}
              className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
              disabled={isLoading}
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="min-h-10 w-full rounded-md bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            {isLoading ? 'Logowanie...' : 'Zaloguj się'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          Nie masz konta?{' '}
          <Link to="/register" className="text-blue-600 hover:text-blue-700">
            Zarejestruj się
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
