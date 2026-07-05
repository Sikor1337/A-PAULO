import { NavLink, Outlet, useLocation } from 'react-router-dom';
import PageShell from '@/components/layout/PageShell';

const tabClass = ({ isActive }: { isActive: boolean }) =>
  `min-w-max flex-1 rounded-lg px-4 py-2.5 text-center text-sm font-bold transition-colors ${
    isActive ? 'bg-white text-indigo-700 shadow-sm' : 'text-gray-500 hover:text-gray-900'
  }`;

const RecruitmentLayout = () => {
  const location = useLocation();
  const inSurveys = location.pathname.startsWith('/recruitment/surveys');
  const departure = location.pathname.includes('/departure/');
  const surveyBase = departure
    ? '/recruitment/surveys/departure'
    : '/recruitment/surveys/recruitment';

  return (
    <PageShell>
      <header className="mb-5 border-b border-gray-200 pb-5">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">Moduł wolontariatu</p>
        <h1 className="mt-1 text-2xl font-bold text-gray-900 sm:text-3xl">Rekrutacja</h1>
        <p className="mt-1 text-sm text-gray-500">Ankiety kandydatów, odejścia i proces wdrażania.</p>
      </header>

      <nav className="mb-4 flex gap-1 overflow-x-auto rounded-xl bg-gray-100 p-1" aria-label="Główne sekcje rekrutacji">
        <NavLink to="/recruitment/surveys/recruitment/editor" className={() => tabClass({ isActive: inSurveys })}>Ankiety</NavLink>
        <NavLink to="/recruitment/onboarding" className={tabClass}>Wdrażanie</NavLink>
      </nav>

      {inSurveys && <>
        <nav className="mb-4 grid gap-2 sm:grid-cols-2" aria-label="Rodzaj ankiety">
          <NavLink to="/recruitment/surveys/recruitment/editor" className={({ isActive }) => `rounded-xl border px-4 py-3 text-center text-sm font-bold ${!departure || isActive ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'text-gray-500 hover:bg-gray-50'}`}>Rekrutacja</NavLink>
          <NavLink to="/recruitment/surveys/departure/editor" className={({ isActive }) => `rounded-xl border px-4 py-3 text-center text-sm font-bold ${departure || isActive ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'text-gray-500 hover:bg-gray-50'}`}>Ankieta odejścia</NavLink>
        </nav>
        <nav className="mb-6 flex gap-1 border-b" aria-label="Widok ankiety">
          <NavLink to={`${surveyBase}/editor`} className={({ isActive }) => `border-b-2 px-5 py-3 text-sm font-bold ${isActive ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500'}`}>Edycja</NavLink>
          <NavLink to={`${surveyBase}/responses`} className={({ isActive }) => `border-b-2 px-5 py-3 text-sm font-bold ${isActive ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500'}`}>Odpowiedzi</NavLink>
        </nav>
      </>}
      <Outlet />
    </PageShell>
  );
};

export default RecruitmentLayout;
