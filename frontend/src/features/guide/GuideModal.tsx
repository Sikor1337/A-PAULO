import { useMemo, useState } from 'react';
import Modal from '@/components/ui/Modal';
import { useMyPermissions } from '@/hooks/usePermissions';
import { useAuthStore } from '@/stores/authStore';
import { guideSections } from './guideContent';

/** In-app guide (PAP-75): a per-module overview reachable from the avatar menu. */
const GuideModal = ({ onClose }: { onClose: () => void }) => {
  const permissions = useMyPermissions().data?.permissions;
  const isAdmin = useAuthStore((state) => state.user?.status) === 'admin';

  const sections = useMemo(() => {
    const granted = permissions ?? [];
    return guideSections.filter((section) => {
      if (section.permission && !granted.includes(section.permission)) return false;
      if (section.adminOnly && !isAdmin) return false;
      return true;
    });
  }, [permissions, isAdmin]);

  const [activeKey, setActiveKey] = useState(guideSections[0]?.key ?? '');
  const active = sections.find((section) => section.key === activeKey) ?? sections[0];

  return (
    <Modal onClose={onClose} maxWidth="max-w-4xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Przewodnik po platformie</h2>
          <p className="mt-1 text-sm text-gray-500">Krótki opis modułów i najważniejszych akcji.</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md px-2 py-1 text-2xl leading-none text-gray-400 hover:text-gray-700"
          aria-label="Zamknij przewodnik"
        >
          &times;
        </button>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-[220px_1fr]">
        <nav className="flex gap-2 overflow-x-auto pb-2 sm:max-h-[60vh] sm:flex-col sm:overflow-y-auto sm:pb-0" aria-label="Moduły">
          {sections.map((section) => (
            <button
              key={section.key}
              type="button"
              onClick={() => setActiveKey(section.key)}
              className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-semibold transition-colors sm:shrink ${
                active?.key === section.key
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="w-5 shrink-0 text-center">{section.icon}</span>
              <span className="whitespace-nowrap sm:whitespace-normal">{section.title}</span>
            </button>
          ))}
        </nav>

        <section className="sm:max-h-[60vh] sm:overflow-y-auto sm:pr-1">
          {active && (
            <>
              <h3 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                <span>{active.icon}</span>
                {active.title}
              </h3>
              <p className="mt-1 text-sm text-gray-600">{active.intro}</p>
              <dl className="mt-4 space-y-3">
                {active.topics.map((topic) => (
                  <div key={topic.heading} className="rounded-xl border border-gray-100 bg-gray-50 p-3">
                    <dt className="text-sm font-bold text-gray-800">{topic.heading}</dt>
                    <dd className="mt-1 text-sm leading-6 text-gray-600">{topic.body}</dd>
                  </div>
                ))}
              </dl>
            </>
          )}
        </section>
      </div>
    </Modal>
  );
};

export default GuideModal;
