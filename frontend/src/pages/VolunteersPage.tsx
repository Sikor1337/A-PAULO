import { useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import DataTable from '@/components/ui/DataTable';
import DetailModal from '@/components/ui/DetailModal';
import { useVolunteers } from '@/hooks/useVolunteers';
import { useGroupList } from '@/hooks/useGroups';
import { useTableControls } from '@/hooks/useTableControls';
import { buildVolunteerColumns } from '@/features/volunteers/volunteerColumns';
import { volunteerDetailFields } from '@/features/volunteers/volunteerDetail';
import VolunteerFormModal from '@/features/volunteers/VolunteerFormModal';
import { exportRowsToCsv } from '@/lib/csv';
import type { Volunteer, VolunteerStatus } from '@/types';

const VolunteersPage: React.FC = () => {
  const [editing, setEditing] = useState<Volunteer | null>(null);
  const [details, setDetails] = useState<Volunteer | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [filterGroup, setFilterGroup] = useState('');
  const [filterStatus, setFilterStatus] = useState<'' | VolunteerStatus>('');

  const closeForm = () => {
    setEditing(null);
    setIsAdding(false);
  };
  const { data, isLoading, save, remove } = useVolunteers({ onSaved: closeForm });
  const { data: groups } = useGroupList();

  const { search, setSearch, toggleSort, sortIcon, rows } = useTableControls(data, {
    searchFields: ['full_name', 'email', 'phone', 'status'],
    initialSort: 'full_name',
    filterPredicate: (v) => {
      const assignedGroups = typeof v.assigned_groups === 'string' ? v.assigned_groups : '';
      if (filterGroup && !(v.led_group === filterGroup || assignedGroups.split(', ').includes(filterGroup))) return false;
      if (filterStatus && v.status !== filterStatus) return false;
      return true;
    },
  });

  const columns = buildVolunteerColumns({
    onSelect: setDetails,
    onEdit: setEditing,
    onDelete: remove.mutate,
  });

  const exportVolunteers = () => {
    exportRowsToCsv(
      'wolontariusze.csv',
      [
        { header: 'Imię i nazwisko', value: (v) => v.full_name },
        { header: 'Email', value: (v) => v.email },
        { header: 'Telefon', value: (v) => v.phone },
        { header: 'Grupa', value: (v) => [v.assigned_groups, v.led_group].filter(Boolean).join(', ') },
        {
          header: 'Funkcja',
          value: (v) =>
            [
              ...(v.led_group ? [`Przewodnik: ${v.led_group}`] : []),
              ...(v.main_for_beneficiaries ?? []).map((name) => `Lider podopiecznego: ${name}`),
            ].join(', '),
        },
        { header: 'Rola', value: (v) => v.role_name },
        { header: 'Status', value: (v) => v.status },
        { header: 'Data przystąpienia', value: (v) => v.join_date },
      ],
      rows,
    );
  };

  return (
    <PageShell>
      <div className="flex items-center justify-between mb-6 border-b pb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🙋</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Wolontariusze</h1>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={exportVolunteers}
            className="border border-gray-200 text-gray-600 px-4 py-2 rounded-lg font-bold text-sm hover:bg-gray-50 transition-all"
          >
            Eksport CSV
          </button>
          <button
            onClick={() => setIsAdding(true)}
            className="bg-[#10b981] text-white px-6 py-2 rounded-lg font-bold text-sm hover:opacity-90 transition-all flex items-center gap-2"
          >
            + Dodaj
          </button>
        </div>
      </div>

      <div className="mb-4 flex gap-2 items-center">
        <input
          type="text"
          placeholder="Szukaj po nazwisku, emailu, telefonie..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-4 h-10 border border-gray-200 rounded-lg bg-gray-50 focus:bg-white focus:border-indigo-500 outline-none text-sm font-medium"
        />
        <select
          value={filterGroup}
          onChange={(e) => setFilterGroup(e.target.value)}
          className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[150px]"
        >
          <option value="">Wszystkie grupy</option>
          {groups?.map((g) => (
            <option key={g.id} value={g.name}>
              {g.name}
            </option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as '' | VolunteerStatus)}
          className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[130px]"
        >
          <option value="">Wszystkie statusy</option>
          <option value="Aktywny">Aktywny</option>
          <option value="Były">Były</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={isLoading}
        getRowKey={(v) => v.id}
        toggleSort={toggleSort}
        sortIcon={sortIcon}
      />

      {details && (
        <DetailModal
          title={details.full_name}
          fields={volunteerDetailFields(details)}
          onClose={() => setDetails(null)}
          footer={
            <>
              <button
                onClick={() => {
                  setEditing(details);
                  setDetails(null);
                }}
                className="bg-[#6366f1] text-white px-4 py-2 rounded-md font-bold hover:opacity-90"
              >
                ✏️ Edytuj
              </button>
              <button onClick={() => setDetails(null)} className="px-4 py-2 text-gray-400 font-bold">
                Zamknij
              </button>
            </>
          }
        />
      )}

      {(editing || isAdding) && (
        <VolunteerFormModal volunteer={editing} onClose={closeForm} onSave={save.mutate} isPending={save.isPending} />
      )}
    </PageShell>
  );
};

export default VolunteersPage;
