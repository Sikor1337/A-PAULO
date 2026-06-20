import { useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import DataTable from '@/components/ui/DataTable';
import DetailModal from '@/components/ui/DetailModal';
import { useBeneficiaries } from '@/hooks/useBeneficiaries';
import { useGroupList } from '@/hooks/useGroups';
import { useTableControls } from '@/hooks/useTableControls';
import { buildBeneficiaryColumns } from '@/features/beneficiaries/beneficiaryColumns';
import { beneficiaryDetailFields } from '@/features/beneficiaries/beneficiaryDetail';
import BeneficiaryFormModal from '@/features/beneficiaries/BeneficiaryFormModal';
import { exportRowsToCsv } from '@/lib/csv';
import type { Beneficiary } from '@/types';

const BeneficiariesPage: React.FC = () => {
  const [editing, setEditing] = useState<Beneficiary | null>(null);
  const [details, setDetails] = useState<Beneficiary | null>(null);
  const [isAdding, setIsAdding] = useState(false);
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
      <div className="flex items-center justify-between mb-6 border-b pb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📄</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Podopieczni</h1>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={exportBeneficiaries}
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
          placeholder="Szukaj po nazwisku, adresie, telefonie..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-4 h-10 border border-gray-200 rounded-lg bg-gray-50 focus:bg-white focus:border-indigo-500 outline-none text-sm font-medium"
        />
        <select
          value={filterGroup}
          onChange={(e) => setFilterGroup(e.target.value === '' ? '' : Number(e.target.value))}
          className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[150px]"
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
          className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[120px]"
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
        <BeneficiaryFormModal beneficiary={editing} onClose={closeForm} onSave={save.mutate} isPending={save.isPending} />
      )}
    </PageShell>
  );
};

export default BeneficiariesPage;
