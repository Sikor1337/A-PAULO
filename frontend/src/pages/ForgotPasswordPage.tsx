import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { authService } from '../services/authService';
import { parseApiError } from '../lib/errors';

interface FormData {
  email: string;
}

const ForgotPasswordPage = () => {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError('');
    try {
      await authService.requestPasswordReset(data.email);
      setSent(true);
    } catch (err) {
      setError(parseApiError(err, 'Wystąpił błąd. Spróbuj ponownie.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-100 px-4 py-6">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-md sm:p-8">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">A-PAULO</h1>
        <h2 className="mb-6 text-center text-xl text-gray-600">Reset hasła</h2>

        {sent ? (
          <>
            <p className="mb-6 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
              Jeśli konto o tym adresie istnieje, wysłaliśmy na nie link do resetu hasła.
              Sprawdź swoją skrzynkę.
            </p>
            <Link to="/login" className="text-blue-600 hover:text-blue-700">
              Powrót do logowania
            </Link>
          </>
        ) : (
          <>
            {error && (
              <div className="mb-4 rounded-md border border-red-400 bg-red-100 p-3 text-red-700">
                {error}
              </div>
            )}
            <p className="mb-4 text-sm text-gray-600">
              Podaj adres e-mail przypisany do konta. Wyślemy link do ustawienia nowego hasła.
            </p>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
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
              <button
                type="submit"
                disabled={isLoading}
                className="min-h-10 w-full rounded-md bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
              >
                {isLoading ? 'Wysyłanie…' : 'Wyślij link'}
              </button>
            </form>
            <p className="mt-4 text-center text-sm text-gray-600">
              <Link to="/login" className="text-blue-600 hover:text-blue-700">
                Powrót do logowania
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
