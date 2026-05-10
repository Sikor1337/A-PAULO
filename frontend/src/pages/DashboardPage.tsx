import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { beneficiaryService } from '../services/beneficiaryService';
import { volunteerService } from '../services/volunteerService';
import Sidebar from '../components/Sidebar';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const { data: beneficiaries } = useQuery({
    queryKey: ['beneficiaries'],
    queryFn: beneficiaryService.getAll
  });

  const { data: volunteers } = useQuery({
    queryKey: ['volunteers'],
    queryFn: volunteerService.getAll
  });

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: 'var(--bg-dark)' }}>
      <Sidebar />

      <div className="ml-[260px] flex-1 p-12">
        <header className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-4xl font-bold mb-2" style={{ color: 'var(--accent-blue)' }}>Dashboard</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Witaj ponownie, {user?.email}</p>
          </div>
          <button onClick={handleLogout} className="px-6 py-2 rounded-lg font-bold bg-red-600 text-white hover:bg-red-700 transition-colors">
            Wyloguj
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            onClick={() => navigate('/beneficiaries')}
            className="p-8 rounded-2xl border cursor-pointer transition-all hover:scale-[1.02]"
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
          >
            <h2 className="text-xs uppercase font-bold mb-4" style={{ color: 'var(--text-secondary)' }}>Podopieczni</h2>
            <p className="text-5xl font-black" style={{ color: 'var(--accent-blue)' }}>
              {beneficiaries?.length || 0}
            </p>
          </div>

          <div
            onClick={() => navigate('/volunteers')}
            className="p-8 rounded-2xl border cursor-pointer transition-all hover:scale-[1.02]"
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
          >
            <h2 className="text-xs uppercase font-bold mb-4" style={{ color: 'var(--text-secondary)' }}>Wolontariusze</h2>
            <p className="text-5xl font-black" style={{ color: 'var(--accent-purple)' }}>
              {volunteers?.length || 0}
            </p>
          </div>

          <div className="p-8 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
            <h2 className="text-xs uppercase font-bold mb-4" style={{ color: 'var(--text-secondary)' }}>Grupy</h2>
            <p className="text-5xl font-black" style={{ color: 'var(--accent-green)' }}>0</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
