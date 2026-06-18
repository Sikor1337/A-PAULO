import type { Column } from '@/components/ui/DataTable';
import StatusBadge from '@/components/ui/StatusBadge';
import type { Volunteer } from '@/types';

interface Handlers {
  onSelect: (v: Volunteer) => void;
  onEdit: (v: Volunteer) => void;
  onDelete: (id: number) => void;
}

const statusColor = (status: Volunteer['status']) =>
  status === 'Aktywny' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';

export function buildVolunteerColumns({ onSelect, onEdit, onDelete }: Handlers): Column<Volunteer>[] {
  return [
    {
      id: 'full_name',
      header: 'Imię i nazwisko',
      widthClass: 'w-[20%]',
      sortKey: 'full_name',
      cellClassName: 'font-medium text-indigo-700 cursor-pointer hover:underline',
      onClick: onSelect,
      render: (v) => v.full_name,
    },
    {
      id: 'email',
      header: 'Email',
      widthClass: 'w-[20%]',
      sortKey: 'email',
      cellClassName: 'text-gray-500',
      render: (v) => v.email || '—',
    },
    {
      id: 'phone',
      header: 'Tel',
      widthClass: 'w-[15%]',
      sortKey: 'phone',
      cellClassName: 'text-gray-500',
      render: (v) => v.phone || '—',
    },
    {
      id: 'assigned_groups',
      header: 'Grupa',
      widthClass: 'w-[15%]',
      align: 'center',
      sortKey: 'assigned_groups',
      render: (v) => {
        const hasNothing = !v.led_group && (!v.main_for_beneficiaries || v.main_for_beneficiaries.length === 0) && !v.assigned_groups;
        return (
          <div className="flex flex-col items-center gap-1">
            {v.led_group && (
              <span className="bg-indigo-100 text-indigo-700 text-[10px] px-2 py-0.5 rounded font-bold uppercase" title="Lider Grupy">
                👑 {v.led_group}
              </span>
            )}
            {v.main_for_beneficiaries?.map((bName) => (
              <span
                key={bName}
                className="bg-amber-100 text-amber-800 text-[10px] px-2 py-0.5 rounded font-bold uppercase flex items-center gap-0.5"
                title={`Główny wolontariusz dla: ${bName}`}
              >
                ⭐ {bName}
              </span>
            ))}
            {v.assigned_groups && <span className="text-gray-500 text-xs">{v.assigned_groups}</span>}
            {hasNothing && <span className="text-gray-400">—</span>}
          </div>
        );
      },
    },
    {
      id: 'status',
      header: 'Status',
      widthClass: 'w-[10%]',
      sortKey: 'status',
      render: (v) => <StatusBadge status={v.status} colorClass={statusColor(v.status)} />,
    },
    {
      id: 'actions',
      header: 'Akcje',
      widthClass: 'w-[10%] min-w-[100px]',
      align: 'center',
      render: (v) => (
        <div className="flex justify-center gap-2">
          <button onClick={() => onEdit(v)} className="bg-[#6366f1] text-white p-1.5 rounded hover:opacity-80">
            ✏️
          </button>
          <button
            onClick={() => {
              if (confirm('Usunąć?')) onDelete(v.id);
            }}
            className="bg-[#ef4444] text-white p-1.5 rounded hover:opacity-80"
          >
            🗑️
          </button>
        </div>
      ),
    },
  ];
}
