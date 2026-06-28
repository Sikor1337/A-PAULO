import { useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface SidebarProps {
  groupsSlot?: ReactNode;
  isOpen?: boolean;
  onClose?: () => void;
}

interface SidebarItem {
  name: string;
  icon: string;
  path: string;
  adminOnly?: boolean;
}

interface SidebarSection {
  title: string;
  items: SidebarItem[];
}

const sections: SidebarSection[] = [
  {
    title: 'ZARZĄDZANIE',
    items: [
      { name: 'Dashboard', icon: '📊', path: '/' },
      { name: 'Podopieczni', icon: '📄', path: '/beneficiaries' },
      { name: 'Wolontariusze', icon: '🙋', path: '/volunteers' },
      { name: 'Grupy', icon: '👥', path: '/groups' },
      { name: 'Karty BO', icon: 'BO', path: '/bo-cards' },
      { name: 'Rekrutacja', icon: 'R', path: '/recruitment' },
    ],
  },
  {
    title: 'OPERACJE',
    items: [
      { name: 'Wydarzenia', icon: '📅', path: '/events' },
      { name: 'Zadania', icon: '📋', path: '/tasks' },
    ],
  },
  {
    title: 'ADMIN',
    items: [{ name: 'Ustawienia', icon: '⚙', path: '/settings', adminOnly: true }],
  },
];

const Sidebar = ({ groupsSlot, isOpen = true, onClose }: SidebarProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/' || location.pathname === '/dashboard';
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  const goTo = (path: string) => {
    navigate(path);
    onClose?.();
  };

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-dvh w-[260px] flex-col transition-transform duration-200 lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
      style={{ backgroundColor: '#1e2330' }}
      aria-label="Nawigacja"
    >
      <div className="flex-1 overflow-y-auto p-5 sm:p-6">
        <div className="mb-8 flex items-center justify-between gap-3 text-sm text-white opacity-80">
          <div className="flex min-w-0 items-center gap-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#2d3345] text-sm font-black text-blue-200">
              💙
            </span>
            <span className="truncate font-bold tracking-tight">A PAULO - Wolontariat v1.0</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-xl leading-none text-gray-300 hover:bg-[#2d3345] hover:text-white lg:hidden"
            aria-label="Zamknij menu"
          >
            &times;
          </button>
        </div>

        {sections.map((section) => (
          <div key={section.title} className="mb-8">
            <h3 className="mb-4 px-2 text-[10px] font-bold tracking-[0.2em] text-gray-500">
              {section.title}
            </h3>
            <nav className="space-y-0.5">
              {section.items
                .filter((item) => !item.adminOnly || user?.role === 'admin')
                .map((item) => (
                  <div
                    key={item.name}
                    role="button"
                    tabIndex={0}
                    onClick={() => goTo(item.path)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        goTo(item.path);
                      }
                    }}
                    className={`flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-left transition-all ${
                      isActive(item.path)
                        ? 'bg-[#2d3345] text-white font-semibold'
                        : 'text-gray-300 hover:bg-[#2d3345] hover:text-white'
                    }`}
                  >
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-white/5 text-xs font-black opacity-80">
                      {item.icon}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-sm font-medium">{item.name}</span>
                    {item.path === '/groups' && groupsSlot && (
                      <div className="ml-auto shrink-0" onClick={(e) => e.stopPropagation()}>
                        {groupsSlot}
                      </div>
                    )}
                  </div>
                ))}
            </nav>
          </div>
        ))}
      </div>

      <div className="relative shrink-0 border-t border-white/10 p-3">
        <button
          type="button"
          onClick={() => setProfileMenuOpen((prev) => !prev)}
          className="flex min-h-12 w-full items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-[#2d3345]"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">
            {(user?.first_name?.[0] || user?.email?.[0] || '?').toUpperCase()}
          </div>
          <div className="min-w-0 flex-1 text-left">
            <p className="truncate text-sm font-semibold text-white">
              {user?.first_name ? `${user.first_name} ${user.last_name}`.trim() : user?.email}
            </p>
            <p className="truncate text-[10px] text-gray-400">{user?.email}</p>
          </div>
          <span className="shrink-0 text-xs text-gray-500">▾</span>
        </button>

        {profileMenuOpen && (
          <div
            className="absolute bottom-full left-3 right-3 z-50 mb-1 rounded-xl border border-white/10 bg-[#2d3345] py-1.5 shadow-2xl"
            onMouseLeave={() => setProfileMenuOpen(false)}
          >
            <button
              type="button"
              onClick={() => {
                setProfileMenuOpen(false);
                goTo('/profile');
              }}
              className="w-full px-3 py-2 text-left text-sm font-medium text-gray-200 transition-colors hover:bg-[#3d4558] hover:text-white"
            >
              👤 Moje konto
            </button>
            <button
              type="button"
              onClick={() => {
                setProfileMenuOpen(false);
                logout();
                goTo('/login');
              }}
              className="w-full px-3 py-2 text-left text-sm font-medium text-rose-400 transition-colors hover:bg-[#3d4558] hover:text-rose-300"
            >
              🚪 Wyloguj
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
