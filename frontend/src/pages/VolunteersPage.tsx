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
import DepartureInterviewModal from '@/features/recruitment/DepartureInterviewModal';
import { exportRowsToCsv } from '@/lib/csv';
import type { Volunteer, VolunteerStatus } from '@/types';

const VolunteersPage: React.FC = () => {
  const [editing, setEditing] = useState<Volunteer | null>(null);
  const [details, setDetails] = useState<Volunteer | null>(null);
  const [departing, setDeparting] = useState<Volunteer | null>(null);
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
    searchFields: ['full_name', 'email', 'phone', 'functions', 'status'],
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
        { header: 'Funkcje', value: (v) => v.functions?.join(', ') },
        { header: 'Status', value: (v) => v.status },
        { header: 'Data przystąpienia', value: (v) => v.join_date },
      ],
      rows,
    );
  };

  return (
    <PageShell>
      <div className="mb-6 flex flex-col gap-4 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🙋</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Wolontariusze</h1>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex">
          <button
            type="button"
            onClick={exportVolunteers}
            className="min-h-10 rounded-lg border border-gray-200 px-4 py-2 text-sm font-bold text-gray-600 transition-all hover:bg-gray-50"
          >
            Eksport CSV
          </button>
          <button
            onClick={() => setIsAdding(true)}
            className="flex min-h-10 items-center justify-center gap-2 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white transition-all hover:opacity-90"
          >
            + Dodaj
          </button>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:flex lg:items-center">
        <input
          type="text"
          placeholder="Szukaj po nazwisku, emailu, telefonie..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-4 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white lg:flex-1"
        />
        <select
          value={filterGroup}
          onChange={(e) => setFilterGroup(e.target.value)}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 lg:w-auto lg:min-w-[150px]"
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
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 lg:w-auto lg:min-w-[130px]"
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
              {details.status === 'Aktywny' && (
                <button
                  onClick={() => {
                    setDeparting(details);
                    setDetails(null);
                  }}
                  className="rounded-md bg-amber-600 px-4 py-2 font-bold text-white hover:opacity-90"
                >
                  Oznacz odejście
                </button>
              )}
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
      {departing && (
        <DepartureInterviewModal volunteer={departing} onClose={() => setDeparting(null)} />
      )}
    </PageShell>
  );
};

export default VolunteersPage;
