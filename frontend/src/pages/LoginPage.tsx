import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/authService';

interface LoginFormData {
  email: string;
  password: string;
}

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuthStore();
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>();

  // Przekieruj jeśli już zalogowany
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');

    try {
      // Pobierz tokeny z backendu
      const { access, refresh } = await authService.login(data);

      // Zapisz tymczasowo tokeny aby pobrać profil
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
          role: userProfile.status === 'admin' ? 'admin' as const : 'volunteer' as const,
        };

        // Update store with user data
        login(access, refresh, user);
      } catch (profileError) {
        // Clear tokens if profile fetch fails
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        throw profileError;
      }

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      if (err.response?.status === 401) {
        setError('Nieprawidłowy email lub hasło');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Wystąpił błąd podczas logowania. Spróbuj ponownie.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center mb-6">A-PAULO</h1>
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Logowanie...' : 'Zaloguj się'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
