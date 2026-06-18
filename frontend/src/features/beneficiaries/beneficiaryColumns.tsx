import type { Column } from '@/components/ui/DataTable';
import StatusBadge from '@/components/ui/StatusBadge';
import type { Beneficiary } from '@/types';

interface Handlers {
  onSelect: (b: Beneficiary) => void;
  onEdit: (b: Beneficiary) => void;
  onDelete: (id: number) => void;
}

const statusColor = (status: Beneficiary['status']) => {
  switch (status) {
    case 'OBECNY':
      return 'bg-green-100 text-green-700';
    case 'ZMARŁY':
      return 'bg-gray-200 text-gray-600';
    case 'DPS_ZOL':
      return 'bg-yellow-100 text-yellow-700';
    default:
      return 'bg-red-100 text-red-700';
  }
};

export function buildBeneficiaryColumns({ onSelect, onEdit, onDelete }: Handlers): Column<Beneficiary>[] {
  return [
    {
      id: 'full_name',
      header: 'Imię i nazwisko',
      widthClass: 'w-[20%]',
      sortKey: 'full_name',
      cellClassName: 'font-medium text-indigo-700 cursor-pointer hover:underline',
      onClick: onSelect,
      render: (b) => b.full_name,
    },
    {
      id: 'address',
      header: 'Adres',
      widthClass: 'w-[25%]',
      sortKey: 'address',
      cellClassName: 'text-gray-500',
      render: (b) => b.address || '—',
    },
    {
      id: 'phone',
      header: 'Tel',
      widthClass: 'w-[15%]',
      sortKey: 'phone',
      cellClassName: 'text-gray-500',
      render: (b) => b.phone || '—',
    },
    {
      id: 'group_name',
      header: 'Grupa',
      widthClass: 'w-[15%]',
      align: 'center',
      sortKey: 'group_name',
      cellClassName: 'text-gray-400',
      render: (b) => b.group_name || '—',
    },
    {
      id: 'bo_enrolled',
      header: 'BO',
      widthClass: 'w-[5%]',
      align: 'center',
      sortKey: 'bo_enrolled',
      cellClassName: 'text-xs font-bold',
      render: (b) => <span className={b.bo_enrolled ? 'text-green-600' : 'text-gray-400'}>{b.bo_enrolled ? 'TAK' : 'NIE'}</span>,
    },
    {
      id: 'status',
      header: 'Status',
      widthClass: 'w-[10%]',
      sortKey: 'status',
      render: (b) => <StatusBadge status={b.status} colorClass={statusColor(b.status)} />,
    },
    {
      id: 'actions',
      header: 'Akcje',
      widthClass: 'w-[10%] min-w-[100px]',
      align: 'center',
      render: (b) => (
        <div className="flex justify-center gap-2">
          <button onClick={() => onEdit(b)} className="bg-[#6366f1] text-white p-1.5 rounded hover:opacity-80">
            ✏️
          </button>
          <button
            onClick={() => {
              if (confirm('Usunąć?')) onDelete(b.id);
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
