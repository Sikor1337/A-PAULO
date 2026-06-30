import { NavLink, Outlet } from 'react-router-dom';
import PageShell from '@/components/layout/PageShell';

const tabs = [
  { path: '/recruitment/form', label: 'Formularz' },
  { path: '/recruitment/responses', label: 'Odpowiedzi' },
  { path: '/recruitment/onboarding', label: 'Wdrażanie' },
];

const RecruitmentLayout = () => (
  <PageShell>
    <header className="mb-5 border-b border-gray-200 pb-5">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">Moduł wolontariatu</p>
      <h1 className="mt-1 text-2xl font-bold text-gray-900 sm:text-3xl">Rekrutacja</h1>
      <p className="mt-1 text-sm text-gray-500">Od pierwszego formularza do zakończenia wdrażania.</p>
    </header>
    <nav className="mb-6 flex gap-1 overflow-x-auto rounded-xl bg-gray-100 p-1" aria-label="Sekcje rekrutacji">
      {tabs.map((tab) => (
        <NavLink
          key={tab.path}
          to={tab.path}
          className={({ isActive }) => `min-w-max flex-1 rounded-lg px-4 py-2.5 text-center text-sm font-bold transition-colors ${
            isActive ? 'bg-white text-indigo-700 shadow-sm' : 'text-gray-500 hover:text-gray-900'
          }`}
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
    <Outlet />
  </PageShell>
);

export default RecruitmentLayout;
