import { useState } from 'react';
import type { ReactNode } from 'react';
import Sidebar from '@/components/Sidebar';

interface PageShellProps {
  /** Page content, rendered inside the main card. */
  children: ReactNode;
  /** Optional node injected into the Sidebar's Groups row (used by GroupsPage). */
  sidebarSlot?: ReactNode;
  /** Override the main card classes (GroupsPage and Dashboard use custom shells). */
  cardClassName?: string;
}

const DEFAULT_CARD = 'min-h-[calc(100dvh-88px)] rounded-xl bg-white p-4 shadow-lg sm:p-6 lg:min-h-[calc(100dvh-48px)]';

const PageShell = ({ children, sidebarSlot, cardClassName = DEFAULT_CARD }: PageShellProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-dvh bg-[#1e2330]">
      <Sidebar groupsSlot={sidebarSlot} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {sidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          aria-label="Zamknij menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-h-dvh flex-col lg:ml-[260px]">
        <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between border-b border-white/10 bg-[#1e2330]/95 px-4 text-white backdrop-blur lg:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="flex h-10 w-10 flex-col items-center justify-center gap-1 rounded-lg border border-white/10 hover:bg-white/10"
            aria-label="Otwórz menu"
          >
            <span className="h-0.5 w-5 rounded-full bg-white" />
            <span className="h-0.5 w-5 rounded-full bg-white" />
            <span className="h-0.5 w-5 rounded-full bg-white" />
          </button>
          <span className="text-sm font-bold tracking-tight">A PAULO</span>
          <span className="h-10 w-10" aria-hidden="true" />
        </header>

        <main className="flex-1 p-3 text-gray-800 sm:p-4 lg:p-6">
          <div className={cardClassName}>{children}</div>
        </main>
      </div>
    </div>
  );
};

export default PageShell;
