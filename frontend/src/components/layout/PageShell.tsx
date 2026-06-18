import type { ReactNode } from 'react';
import Sidebar from '@/components/Sidebar';

interface PageShellProps {
  /** Page content, rendered inside the white card. */
  children: ReactNode;
  /** Optional node injected into the Sidebar's Groups row (used by GroupsPage). */
  sidebarSlot?: ReactNode;
  /** Override the white card classes (GroupsPage uses a flex-col, padding-less card). */
  cardClassName?: string;
}

const DEFAULT_CARD = 'bg-white rounded-xl shadow-lg min-h-[calc(100vh-48px)] p-6';

/** Shared screen scaffold: dark background, fixed Sidebar, and the main white card. */
const PageShell = ({ children, sidebarSlot, cardClassName = DEFAULT_CARD }: PageShellProps) => (
  <div className="flex min-h-screen bg-[#1e2330]">
    <Sidebar groupsSlot={sidebarSlot} />
    <div className="ml-[260px] flex-1 p-6 text-gray-800">
      <div className={cardClassName}>{children}</div>
    </div>
  </div>
);

export default PageShell;
