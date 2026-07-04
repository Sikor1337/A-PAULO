import { Navigate, useParams } from 'react-router-dom';
import {
  clearRecruitmentAccessToken,
  isRecruitmentTokenShapeValid,
  storeRecruitmentAccessToken,
} from '@/lib/recruitmentAccess';
import { useAuthStore } from '@/stores/authStore';
import RecruitmentApplicationPage from './RecruitmentApplicationPage';

const RecruitmentEntryPage = () => {
  const { token } = useParams<{ token: string }>();
  const { isAuthenticated, user } = useAuthStore();
  const isValidToken = isRecruitmentTokenShapeValid(token);

  if (isValidToken) storeRecruitmentAccessToken(token);

  if (!isValidToken) {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-gray-100 p-4">
        <section className="max-w-lg rounded-2xl bg-white p-8 text-center shadow-xl">
          <h1 className="text-2xl font-bold text-gray-900">Nieprawidłowy link</h1>
          <p className="mt-3 text-gray-600">Poproś o ponowne przesłanie linku do ankiety rekrutacyjnej.</p>
        </section>
      </main>
    );
  }
  if (!isAuthenticated || !user) {
    return <Navigate to="/login?recruitment=1" replace />;
  }
  if (user.status !== 'new_volunteer') {
    clearRecruitmentAccessToken();
    return <Navigate to="/dashboard" replace />;
  }
  return <RecruitmentApplicationPage accessToken={token} />;
};

export default RecruitmentEntryPage;
