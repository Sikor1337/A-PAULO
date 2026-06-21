import { useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface SidebarProps {
    groupsSlot?: ReactNode;
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

const Sidebar = ({ groupsSlot }: SidebarProps) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuthStore();
    const [profileMenuOpen, setProfileMenuOpen] = useState(false);

    const sections: SidebarSection[] = [
        {
            title: 'ZARZĄDZANIE',
            items: [
                { name: 'Dashboard', icon: '📊', path: '/' },
                { name: 'Podopieczni', icon: '📄', path: '/beneficiaries' },
                { name: 'Wolontariusze', icon: '🙋', path: '/volunteers' },
                { name: 'Grupy', icon: '👥', path: '/groups' },
                { name: 'Wdrażanie', icon: '🚀', path: '/onboarding' },
            ]
        },
        {
            title: 'OPERACJE',
            items: [
                { name: 'Wydarzenia', icon: '📅', path: '/events' },
                { name: 'Zadania', icon: '📋', path: '/tasks' },
            ]
        },
        {
            title: 'ADMIN',
            items: [
                { name: 'Ustawienia', icon: '⚙', path: '/settings', adminOnly: true },
                { name: 'Wizyty', icon: '🏠', path: '/visits' },
                { name: 'Komunikacja', icon: '💬', path: '/communication' },
                { name: 'Fundusze', icon: '💰', path: '/funds' },
            ]
        }
    ];

    const isActive = (path: string) => {
        if (path === '/') return location.pathname === '/' || location.pathname === '/dashboard';
        return location.pathname === path;
    };

    return (
        <div className="w-[260px] h-screen fixed left-0 top-0 flex flex-col" style={{ backgroundColor: '#1e2330' }}>
            <div className="p-6 overflow-y-auto flex-1">
                <div className="flex items-center gap-2 text-white opacity-80 text-sm mb-8">
                    <span>💙</span>
                    <span className="font-bold tracking-tight">A PAULO - Wolontariat v1.0</span>
                </div>

                {sections.map((section) => (
                    <div key={section.title} className="mb-8">
                        <h3 className="text-[10px] font-bold text-gray-500 tracking-[0.2em] mb-4 px-2">
                            {section.title}
                        </h3>
                        <nav className="space-y-0.5">
                            {section.items
                                .filter((item) => !item.adminOnly || user?.role === 'admin')
                                .map((item) => (
                                <div
                                    key={item.name}
                                    onClick={() => navigate(item.path)}
                                    className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all ${
                                        isActive(item.path)
                                            ? 'bg-[#2d3345] text-white font-semibold'
                                            : 'text-gray-300 hover:bg-[#2d3345] hover:text-white'
                                    }`}
                                >
                                    <span className="text-lg opacity-70">{item.icon}</span>
                                    <span className="text-sm font-medium">{item.name}</span>
                                    {item.path === '/groups' && groupsSlot && (
                                        <div className="ml-auto" onClick={e => e.stopPropagation()}>
                                            {groupsSlot}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </nav>
                    </div>
                ))}
            </div>

            <div className="p-3 border-t border-white/10 relative shrink-0">
                <button
                    type="button"
                    onClick={() => setProfileMenuOpen((prev) => !prev)}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#2d3345] transition-colors"
                >
                    <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold text-sm shrink-0">
                        {(user?.first_name?.[0] || user?.email?.[0] || '?').toUpperCase()}
                    </div>
                    <div className="flex-1 text-left min-w-0">
                        <p className="text-sm font-semibold text-white truncate">
                            {user?.first_name ? `${user.first_name} ${user.last_name}`.trim() : user?.email}
                        </p>
                        <p className="text-[10px] text-gray-400 truncate">{user?.email}</p>
                    </div>
                    <span className="text-gray-500 text-xs shrink-0">▾</span>
                </button>

                {profileMenuOpen && (
                    <div
                        className="absolute left-3 right-3 bottom-full mb-1 bg-[#2d3345] rounded-xl shadow-2xl border border-white/10 py-1.5 z-50"
                        onMouseLeave={() => setProfileMenuOpen(false)}
                    >
                        <button
                            type="button"
                            onClick={() => {
                                setProfileMenuOpen(false);
                                navigate('/profile');
                            }}
                            className="w-full text-left px-3 py-2 text-sm font-medium text-gray-200 hover:bg-[#3d4558] hover:text-white transition-colors"
                        >
                            👤 Moje konto
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                setProfileMenuOpen(false);
                                logout();
                                navigate('/login');
                            }}
                            className="w-full text-left px-3 py-2 text-sm font-medium text-rose-400 hover:bg-[#3d4558] hover:text-rose-300 transition-colors"
                        >
                            🚪 Wyloguj
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Sidebar;
