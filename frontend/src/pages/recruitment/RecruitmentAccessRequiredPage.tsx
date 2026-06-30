import { Navigate } from 'react-router-dom';
import { getStoredRecruitmentPath } from '@/lib/recruitmentAccess';

const RecruitmentAccessRequiredPage = () => {
  const path = getStoredRecruitmentPath();
  if (path) return <Navigate to={path} replace />;

  return (
    <main className="flex min-h-dvh items-center justify-center bg-gray-100 p-4">
      <section className="max-w-lg rounded-2xl bg-white p-8 text-center shadow-xl">
        <h1 className="text-2xl font-bold text-gray-900">Otwórz link rekrutacyjny</h1>
        <p className="mt-3 text-gray-600">
          To konto wymaga uzupełnienia ankiety. Otwórz otrzymany link rekrutacyjny, aby kontynuować.
        </p>
      </section>
    </main>
  );
};

export default RecruitmentAccessRequiredPage;
