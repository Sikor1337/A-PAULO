import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { authService } from '../services/authService';
import { parseApiError } from '../lib/errors';

interface FormData {
  password: string;
  confirmPassword: string;
}

const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormData>();
  const password = watch('password');

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError('');
    try {
      await authService.confirmPasswordReset(token, data.password);
      navigate('/login', {
        state: { message: 'Hasło zostało zmienione. Zaloguj się nowym hasłem.' },
      });
    } catch (err) {
      setError(parseApiError(err, 'Link jest nieprawidłowy lub wygasł.'));
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-gray-100 px-4 py-6">
        <div className="w-full max-w-md rounded-lg bg-white p-6 text-center shadow-md sm:p-8">
          <h1 className="mb-6 text-2xl font-bold text-gray-900">A-PAULO</h1>
          <p className="mb-6 text-gray-600">Brak tokenu resetu w linku.</p>
          <Link to="/login" className="text-blue-600 hover:text-blue-700">
            Powrót do logowania
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-100 px-4 py-6">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-md sm:p-8">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">A-PAULO</h1>
        <h2 className="mb-6 text-center text-xl text-gray-600">Ustaw nowe hasło</h2>

        {error && (
          <div className="mb-4 rounded-md border border-red-400 bg-red-100 p-3 text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
              Nowe hasło
            </label>
            <input
              id="password"
              type="password"
              {...register('password', {
                required: 'Hasło jest wymagane',
                minLength: { value: 6, message: 'Hasło musi mieć minimum 6 znaków' },
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
            <label
              htmlFor="confirmPassword"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
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
            {isLoading ? 'Zapisywanie…' : 'Ustaw nowe hasło'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
