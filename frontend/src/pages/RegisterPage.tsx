import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/authService';
import { parseApiError } from '../lib/errors';
import {
  destinationForUser,
  getStoredRecruitmentAccessToken,
} from '../lib/recruitmentAccess';

interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  first_name: string;
  last_name: string;
}

const RegisterPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, user } = useAuthStore();
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>();

  const password = watch('password');

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      navigate(destinationForUser(user.status));
    }
  }, [isAuthenticated, navigate, user]);

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError('');

    try {
      // Register user
      await authService.register({
        username: data.username,
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        recruitment_token: searchParams.get('recruitment') === '1'
          ? getStoredRecruitmentAccessToken()
          : undefined,
      });

      // Redirect to login after successful registration
      navigate('/login', { 
        state: { message: 'Rejestracja zakończona pomyślnie! Zaloguj się na swoje konto.' } 
      });
    } catch (err) {
      console.error('Registration error:', err);
      setError(parseApiError(err, 'Wystąpił błąd podczas rejestracji. Spróbuj ponownie.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-100 px-4 py-6">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-md sm:p-8">
        <h1 className="text-2xl font-bold text-center mb-6 text-gray-900">A-PAULO</h1>
        <h2 className="text-xl text-center mb-6 text-gray-600">Rejestracja</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Nazwa użytkownika
            </label>
            <input
              id="username"
              type="text"
              {...register('username', {
                required: 'Nazwa użytkownika jest wymagana',
                minLength: {
                  value: 3,
                  message: 'Nazwa użytkownika musi mieć minimum 3 znaki',
                },
              })}
              className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="nazwa_uzytkownika"
              disabled={isLoading}
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
            )}
          </div>

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
            <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
              Imię (opcjonalne)
            </label>
            <input
              id="first_name"
              type="text"
              {...register('first_name')}
              className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Jan"
              disabled={isLoading}
            />
          </div>

          <div>
            <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
              Nazwisko (opcjonalne)
            </label>
            <input
              id="last_name"
              type="text"
              {...register('last_name')}
              className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Kowalski"
              disabled={isLoading}
            />
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

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              Potwierdź hasło
            </label>
            <input
              id="confirmPassword"
              type="password"
              {...register('confirmPassword', {
                required: 'Potwierdzenie hasła jest wymagane',
                validate: (value) => value === password || 'Hasła nie są identyczne',
              })}
              className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
              disabled={isLoading}
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="min-h-10 w-full rounded-md bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            {isLoading ? 'Rejestracja...' : 'Utwórz konto'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          Masz już konto?{' '}
          <Link to="/login" className="text-blue-600 hover:text-blue-700">
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
