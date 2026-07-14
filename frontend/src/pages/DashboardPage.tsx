import { useNavigate } from 'react-router-dom';
import PageShell from '@/components/layout/PageShell';
import { useAuthStore } from '../stores/authStore';
import { useBeneficiaryList } from '@/hooks/useBeneficiaries';
import { useVolunteerList } from '@/hooks/useVolunteers';
import { useGroupList } from '@/hooks/useGroups';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { data: beneficiaries } = useBeneficiaryList();
  const { data: volunteers } = useVolunteerList();
  const { data: groups } = useGroupList();

  return (
    <PageShell cardClassName="min-h-[calc(100dvh-88px)] text-white lg:min-h-[calc(100dvh-48px)]">
      <header className="mb-8 sm:mb-12">
        <h1 className="mb-2 text-3xl font-bold sm:text-4xl" style={{ color: 'var(--accent-blue)' }}>
          Dashboard
        </h1>
        <p className="break-words" style={{ color: 'var(--text-secondary)' }}>
          Witaj ponownie, {user?.email}
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 lg:gap-8">
        <button
          type="button"
          onClick={() => navigate('/beneficiaries')}
          className="rounded-lg border p-6 text-left transition-all hover:scale-[1.02] sm:p-8"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
          <h2 className="mb-4 text-xs font-bold uppercase" style={{ color: 'var(--text-secondary)' }}>
            Podopieczni
          </h2>
          <p className="text-4xl font-black sm:text-5xl" style={{ color: 'var(--accent-blue)' }}>
            {beneficiaries?.length || 0}
          </p>
        </button>

        <button
          type="button"
          onClick={() => navigate('/volunteers')}
          className="rounded-lg border p-6 text-left transition-all hover:scale-[1.02] sm:p-8"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
          <h2 className="mb-4 text-xs font-bold uppercase" style={{ color: 'var(--text-secondary)' }}>
            Wolontariusze
          </h2>
          <p className="text-4xl font-black sm:text-5xl" style={{ color: 'var(--accent-purple)' }}>
            {volunteers?.length || 0}
          </p>
        </button>

        <button
          type="button"
          onClick={() => navigate('/groups')}
          className="rounded-lg border p-6 text-left transition-all hover:scale-[1.02] sm:col-span-2 sm:p-8 lg:col-span-1"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
          <h2 className="mb-4 text-xs font-bold uppercase" style={{ color: 'var(--text-secondary)' }}>
            Grupy
          </h2>
          <p className="text-4xl font-black sm:text-5xl" style={{ color: 'var(--accent-green)' }}>
            {groups?.length || 0}
          </p>
        </button>
      </div>
    </PageShell>
  );
};

export default DashboardPage;
