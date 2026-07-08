import { useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import DataTable from '@/components/ui/DataTable';
import DetailModal from '@/components/ui/DetailModal';
import { useBeneficiaries } from '@/hooks/useBeneficiaries';
import { useGroupList } from '@/hooks/useGroups';
import { useTableControls } from '@/hooks/useTableControls';
import { useHasPermission } from '@/hooks/usePermissions';
import { buildBeneficiaryColumns } from '@/features/beneficiaries/beneficiaryColumns';
import { beneficiaryDetailFields } from '@/features/beneficiaries/beneficiaryDetail';
import BeneficiaryFormModal from '@/features/beneficiaries/BeneficiaryFormModal';
import CsvImportModal from '@/features/imports/CsvImportModal';
import HistoryButton from '@/features/audit/HistoryButton';
import { exportRowsToCsv } from '@/lib/csv';
import type { Beneficiary } from '@/types';

const BeneficiariesPage: React.FC = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_BENEFICIARIES');
  const [editing, setEditing] = useState<Beneficiary | null>(null);
  const [details, setDetails] = useState<Beneficiary | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [filterGroup, setFilterGroup] = useState<number | ''>('');
  const [filterBO, setFilterBO] = useState<'' | 'yes' | 'no'>('');

  const closeForm = () => {
    setEditing(null);
    setIsAdding(false);
  };
  const { data, isLoading, save, remove } = useBeneficiaries({ onSaved: closeForm });
  const { data: groups } = useGroupList();

  const { search, setSearch, toggleSort, sortIcon, rows } = useTableControls(data, {
    searchFields: ['full_name', 'address', 'phone', 'status'],
    initialSort: 'full_name',
    comparators: {
      bo_enrolled: (a, b) => (a.bo_enrolled ? 1 : 0) - (b.bo_enrolled ? 1 : 0),
    },
    filterPredicate: (b) => {
      if (filterGroup !== '' && b.group !== filterGroup) return false;
      if (filterBO === 'yes' && b.bo_enrolled !== true) return false;
      if (filterBO === 'no' && b.bo_enrolled) return false;
      return true;
    },
  });

  const columns = buildBeneficiaryColumns({
    onSelect: setDetails,
    onEdit: setEditing,
    onDelete: remove.mutate,
    canManage,
  });

  const exportBeneficiaries = () => {
    exportRowsToCsv(
      'podopieczni.csv',
      [
        { header: 'Imię i nazwisko', value: (b) => b.full_name },
        { header: 'Adres', value: (b) => b.address },
        { header: 'Telefon', value: (b) => b.phone },
        { header: 'Telefon rodziny', value: (b) => b.family_phone },
        { header: 'Grupa', value: (b) => b.group_name },
        { header: 'BO', value: (b) => (b.bo_enrolled ? 'TAK' : 'NIE') },
        { header: 'Status', value: (b) => b.status },
        { header: 'Ostatnia wizyta księdza', value: (b) => b.last_priest_visit },
        { header: 'Ostatnie spotkanie z wolontariuszem', value: (b) => b.last_volunteer_meeting },
      ],
      rows,
    );
  };

  return (
    <PageShell>
      <div className="mb-6 flex flex-col gap-4 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📄</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Podopieczni</h1>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex">
          {canManage && <button
            type="button"
            onClick={exportBeneficiaries}
            className="min-h-10 rounded-lg border border-gray-200 px-4 py-2 text-sm font-bold text-gray-600 transition-all hover:bg-gray-50"
          >
            Eksport CSV
          </button>}
          {canManage && (
            <button
              type="button"
              onClick={() => setIsImporting(true)}
              className="min-h-10 rounded-lg border border-gray-200 px-4 py-2 text-sm font-bold text-gray-600 transition-all hover:bg-gray-50"
            >
              Import CSV
            </button>
          )}
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
          placeholder="Szukaj po nazwisku, adresie, telefonie..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-4 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white lg:flex-1"
        />
        <select
          value={filterGroup}
          onChange={(e) => setFilterGroup(e.target.value === '' ? '' : Number(e.target.value))}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 lg:w-auto lg:min-w-[150px]"
        >
          <option value="">Wszystkie grupy</option>
          {groups?.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
        <select
          value={filterBO}
          onChange={(e) => setFilterBO(e.target.value as '' | 'yes' | 'no')}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 lg:w-auto lg:min-w-[120px]"
        >
          <option value="">BO: Wszystkie</option>
          <option value="yes">BO: TAK</option>
          <option value="no">BO: NIE</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={isLoading}
        getRowKey={(b) => b.id}
        toggleSort={toggleSort}
        sortIcon={sortIcon}
      />

      {details && (
        <DetailModal
          title={details.full_name}
          fields={beneficiaryDetailFields(details)}
          valueClassName="text-gray-700"
          onClose={() => setDetails(null)}
          footer={
            <>
              <HistoryButton
                path={`v1/beneficiaries/${details.id}/audit`}
                entityName={details.full_name}
              />
              {canManage && <button
                onClick={() => {
                  setEditing(details);
                  setDetails(null);
                }}
                className="bg-[#6366f1] text-white px-4 py-2 rounded-md font-bold hover:opacity-90"
              >
                ✏️ Edytuj
              </button>}
              <button onClick={() => setDetails(null)} className="px-4 py-2 text-gray-400 font-bold">
                Zamknij
              </button>
            </>
          }
        />
      )}

      {canManage && (editing || isAdding) && (
        <BeneficiaryFormModal beneficiary={editing} onClose={closeForm} onSave={save.mutate} isPending={save.isPending} />
      )}

      {canManage && isImporting && (
        <CsvImportModal entity="beneficiaries" entityLabel="podopiecznych" onClose={() => setIsImporting(false)} />
      )}
    </PageShell>
  );
};

export default BeneficiariesPage;
