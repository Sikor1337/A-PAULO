import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';
import { parseApiError } from '../lib/errors';

type Status = 'pending' | 'success' | 'error';

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [status, setStatus] = useState<Status>(token ? 'pending' : 'error');
  const [error, setError] = useState(
    token ? '' : 'Brak tokenu weryfikacyjnego w linku.',
  );
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;
    authService
      .verifyEmail(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        setStatus('error');
        setError(parseApiError(err, 'Link jest nieprawidłowy lub wygasł.'));
      });
  }, [token]);

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-100 px-4 py-6">
      <div className="w-full max-w-md rounded-lg bg-white p-6 text-center shadow-md sm:p-8">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">A-PAULO</h1>
        {status === 'pending' && (
          <p className="text-gray-600">Weryfikujemy Twój adres e-mail…</p>
        )}
        {status === 'success' && (
          <>
            <h2 className="mb-3 text-xl font-bold text-emerald-600">Adres potwierdzony</h2>
            <p className="mb-6 text-gray-600">Możesz się teraz zalogować na swoje konto.</p>
            <Link
              to="/login"
              className="inline-block min-h-10 rounded-md bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
            >
              Przejdź do logowania
            </Link>
          </>
        )}
        {status === 'error' && (
          <>
            <h2 className="mb-3 text-xl font-bold text-red-600">Nie udało się potwierdzić</h2>
            <p className="mb-6 text-gray-600">{error}</p>
            <Link
              to="/login"
              className="inline-block min-h-10 rounded-md bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
            >
              Powrót do logowania
            </Link>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;
