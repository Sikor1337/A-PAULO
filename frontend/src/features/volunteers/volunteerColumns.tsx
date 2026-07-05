import type { Column } from '@/components/ui/DataTable';
import GroupNameCell from '@/components/ui/GroupNameCell';
import StatusBadge from '@/components/ui/StatusBadge';
import type { Volunteer } from '@/types';

interface Handlers {
  onSelect: (v: Volunteer) => void;
  onEdit: (v: Volunteer) => void;
  onDelete: (id: number) => void;
  canManage: boolean;
}

const statusColor = (status: Volunteer['status']) =>
  status === 'Aktywny' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';

const splitGroups = (groups: unknown) =>
  (typeof groups === 'string' ? groups : '')
    .split(',')
    .map((group) => group.trim())
    .filter(Boolean);

const uniqueGroups = (v: Volunteer) =>
  Array.from(new Set([...splitGroups(v.assigned_groups), v.led_group].filter((group): group is string => Boolean(group))));

const renderFunctionList = (functions: string[]) => {
  if (functions.length === 0) return <span className="text-gray-400">—</span>;

  return (
    <div className="flex flex-col gap-1">
      {functions.map((label) => (
        <span
          key={label}
          className="bg-gray-100 text-gray-700 text-[11px] px-2 py-0.5 rounded font-semibold leading-snug"
          title={label}
        >
          {label}
        </span>
      ))}
    </div>
  );
};

export function buildVolunteerColumns({ onSelect, onEdit, onDelete, canManage }: Handlers): Column<Volunteer>[] {
  const columns: Column<Volunteer>[] = [
    {
      id: 'full_name',
      header: 'Imię i nazwisko',
      widthClass: 'w-[18%]',
      sortKey: 'full_name',
      cellClassName: 'font-medium text-indigo-700 cursor-pointer hover:underline',
      onClick: onSelect,
      render: (v) => v.full_name,
    },
    {
      id: 'email',
      header: 'Email',
      widthClass: 'w-[18%]',
      sortKey: 'email',
      cellClassName: 'text-gray-500',
      render: (v) => v.email || '—',
    },
    {
      id: 'phone',
      header: 'Tel',
      widthClass: 'w-[12%]',
      sortKey: 'phone',
      cellClassName: 'text-gray-500',
      render: (v) => v.phone || '—',
    },
    {
      id: 'assigned_groups',
      header: 'Grupa',
      widthClass: 'w-[13%]',
      align: 'center',
      sortKey: 'assigned_groups',
      render: (v) => <GroupNameCell value={uniqueGroups(v)} align="center" />,
    },
    {
      id: 'functions',
      header: 'Funkcje',
      widthClass: 'w-[28%]',
      sortKey: 'functions',
      render: (v) => renderFunctionList(v.functions ?? []),
    },
    {
      id: 'status',
      header: 'Status',
      widthClass: 'w-[8%]',
      sortKey: 'status',
      render: (v) => <StatusBadge status={v.status} colorClass={statusColor(v.status)} />,
    },
  ];
  if (canManage) {
    columns.push({
      id: 'actions',
      header: 'Akcje',
      widthClass: 'w-[8%] min-w-[100px]',
      align: 'center',
      render: (v) => (
        <div className="flex justify-center gap-2">
          <button onClick={() => onEdit(v)} className="bg-[#6366f1] text-white p-1.5 rounded hover:opacity-80">
            ✏️
          </button>
          {v.status === 'Aktywny' && (
            <button
              onClick={() => {
                if (confirm('Usunąć?')) onDelete(v.id);
              }}
              className="bg-[#ef4444] text-white p-1.5 rounded hover:opacity-80"
            >
              🗑️
            </button>
          )}
        </div>
      ),
    });
  }
  return columns;
}
