import { useNavigate, useLocation } from 'react-router-dom';

const Sidebar = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const sections = [
        {
            title: 'ZARZĄDZANIE',
            items: [
                { name: 'Dashboard', icon: '📊', path: '/' },
                { name: 'Podopieczni', icon: '📄', path: '/beneficiaries' },
                { name: 'Wolontariusze', icon: '🙋', path: '/volunteers' },
                { name: 'Rekrutacja', icon: '👥', path: '/recruitment' },
                { name: 'Wdrażanie', icon: '🚀', path: '/onboarding' },
            ]
        },
        {
            title: 'OPERACJE',
            items: [
                { name: 'Wydarzenia', icon: '📅', path: '/events' },
                { name: 'Zadania', icon: '📋', path: '/tasks' },
                { name: 'Karty BO', icon: '💳', path: '/cards' },
            ]
        },
        {
            title: 'ADMIN',
            items: [
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
            <div className="p-6">
                <div className="flex items-center gap-2 text-white opacity-80 text-sm mb-8">
                    <span>💙</span>
                    <span className="font-bold tracking-tight">A PAULO - Wolontariat v1.0</span>
                </div>

                {sections.map((section) => (
                    <div key={section.title} className="mb-8">
                        <h3 className="text-[10px] font-bold text-gray-500 tracking-[0.2em] mb-4 px-2">
                            {section.title}
                        </h3>
                        <nav className="space-y-1">
                            {section.items.map((item) => (
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
                                </div>
                            ))}
                        </nav>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Sidebar;
