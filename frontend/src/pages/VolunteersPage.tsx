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
      if (filterGroup && !(v.led_group === filterGroup || v.assigned_groups.split(', ').includes(filterGroup))) return false;
      if (filterStatus && v.status !== filterStatus) return false;
      return true;
    },
  });

  const columns = buildVolunteerColumns({
    onSelect: setDetails,
    onEdit: setEditing,
    onDelete: remove.mutate,
  });

  return (
    <PageShell>
      <div className="flex items-center justify-between mb-6 border-b pb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🙋</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Wolontariusze</h1>
        </div>
        <button
          onClick={() => setIsAdding(true)}
          className="bg-[#10b981] text-white px-6 py-2 rounded-lg font-bold text-sm hover:opacity-90 transition-all flex items-center gap-2"
        >
          + Dodaj
        </button>
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
