import { useState, useMemo } from 'react';
import PageShell from '@/components/layout/PageShell';
import DetailModal from '@/components/ui/DetailModal';
import { useGroups, useGroupDetail } from '@/hooks/useGroups';
import { useVolunteerList } from '@/hooks/useVolunteers';
import { useBeneficiaryList } from '@/hooks/useBeneficiaries';
import { volunteerDetailFields } from '@/features/volunteers/volunteerDetail';
import { beneficiaryDetailFields } from '@/features/beneficiaries/beneficiaryDetail';
import type {
  Volunteer,
  Beneficiary,
  GroupDetail,
  GroupBeneficiary,
  AssignmentVolunteer,
  AssignmentInput,
} from '@/types';

interface VolunteerEntry {
  localId: string;
  volunteerId: number | '';
  isMain: boolean;
  additionalInfo: string;
}

interface BeneficiaryRow {
  localId: string;
  beneficiaryId: number | '';
  volunteers: VolunteerEntry[];
}

const MONTHS_PL = ['Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze', 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru'];
let _rowCounter = 0;
const newRowId = () => `r${++_rowCounter}`;
const emptyVolunteer = (): VolunteerEntry => ({ localId: newRowId(), volunteerId: '', isMain: false, additionalInfo: '' });

/** Builds the editable beneficiary/volunteer rows from a loaded group detail. */
const buildRowsFromDetail = (detail: GroupDetail): BeneficiaryRow[] =>
  (detail.beneficiaries || []).map((b) => ({
    localId: newRowId(),
    beneficiaryId: b.id,
    volunteers: b.volunteers.length
      ? b.volunteers.map((v) => ({ localId: newRowId(), volunteerId: v.id, isMain: v.is_main, additionalInfo: v.additional_info }))
      : [emptyVolunteer()],
  }));

const GROUPS_CARD = 'bg-white rounded-xl shadow-lg min-h-[calc(100vh-48px)] flex flex-col';

const GroupsPage: React.FC = () => {
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [previousGroupId, setPreviousGroupId] = useState<number | null>(null);
  const [showKartyBO, setShowKartyBO] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const [detailBeneficiary, setDetailBeneficiary] = useState<Beneficiary | null>(null);
  const [detailVolunteer, setDetailVolunteer] = useState<Volunteer | null>(null);
  const [kartyBOStatus, setKartyBOStatus] = useState<Record<string, boolean>>({});

  const [benRows, setBenRows] = useState<BeneficiaryRow[]>([]);
  const [formName, setFormName] = useState('');
  const [formLeader, setFormLeader] = useState<number | ''>('');

  const [showBeneficiaryPicker, setShowBeneficiaryPicker] = useState(false);
  const [beneficiaryPickerSearch, setBeneficiaryPickerSearch] = useState('');
  const [sidebarDropdownOpen, setSidebarDropdownOpen] = useState(false);

  const { groups, saveGroup, deleteGroup } = useGroups();
  const { data: volunteers } = useVolunteerList();
  const { data: beneficiaries } = useBeneficiaryList();
  const { data: groupDetail } = useGroupDetail(selectedGroupId);

  const isNewGroup = selectedGroupId === null;

  const months = useMemo(() => {
    const now = new Date();
    return Array.from({ length: 6 }, (_, i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - (5 - i), 1);
      return { key: `${d.getFullYear()}-${d.getMonth() + 1}`, label: `${MONTHS_PL[d.getMonth()]} ${String(d.getFullYear()).slice(2)}` };
    });
  }, []);

  const boEligibleRows = useMemo(() => {
    if (!groupDetail?.beneficiaries || !beneficiaries) return [];
    return groupDetail.beneficiaries
      .filter((b) => beneficiaries.find((fb) => fb.id === b.id)?.bo_enrolled === true)
      .flatMap((b) => b.volunteers.map((v) => ({ beneficiary: b, volunteer: v })));
  }, [groupDetail, beneficiaries]);

  // Auto-select first group on initial load (the condition turns false once set)
  if (groups?.length && selectedGroupId === null && previousGroupId === null) {
    setSelectedGroupId(groups[0].id);
  }

  // Exit edit mode when switching groups — adjust state during render on change
  const [prevSelectedGroupId, setPrevSelectedGroupId] = useState(selectedGroupId);
  if (selectedGroupId !== prevSelectedGroupId) {
    setPrevSelectedGroupId(selectedGroupId);
    setIsEditing(false);
    setShowKartyBO(false);
  }

  // Populate form from groupDetail when a new detail loads
  const [prevGroupDetail, setPrevGroupDetail] = useState(groupDetail);
  if (groupDetail && groupDetail !== prevGroupDetail) {
    setPrevGroupDetail(groupDetail);
    setFormName(groupDetail.name);
    setFormLeader(groupDetail.leader || '');
    setBenRows(buildRowsFromDetail(groupDetail));
  }

  // Clear form when switching into "new group" mode
  const [prevIsNewGroup, setPrevIsNewGroup] = useState(isNewGroup);
  if (isNewGroup !== prevIsNewGroup) {
    setPrevIsNewGroup(isNewGroup);
    if (isNewGroup) {
      setFormName('');
      setFormLeader('');
      setBenRows([]);
    }
  }

  const startNewGroup = () => {
    setPreviousGroupId(selectedGroupId);
    setSelectedGroupId(null);
  };

  const cancelNewGroup = () => {
    setSelectedGroupId(previousGroupId ?? groups?.[0]?.id ?? null);
    setPreviousGroupId(null);
  };

  const enterEditMode = () => {
    if (groupDetail) {
      setFormName(groupDetail.name);
      setFormLeader(groupDetail.leader || '');
      setBenRows(buildRowsFromDetail(groupDetail));
    }
    setIsEditing(true);
  };

  const handleDeleteGroup = () => {
    if (selectedGroupId === null) return;
    const name = groups?.find((g) => g.id === selectedGroupId)?.name ?? '';
    if (confirm(`Usunąć grupę „${name}"? Podopieczni zostaną odłączeni, a ich przypisania wolontariuszy usunięte.`)) {
      deleteGroup.mutate(selectedGroupId, {
        onSuccess: () => {
          setPreviousGroupId(null);
          setIsEditing(false);
          setSelectedGroupId(groups?.find((g) => g.id !== selectedGroupId)?.id ?? null);
        },
      });
    }
  };

  const handleFormSubmit = (e: React.BaseSyntheticEvent) => {
    e.preventDefault();
    const assignments: AssignmentInput[] = benRows
      .filter((row) => row.beneficiaryId !== '')
      .map((row) => {
        const vols = row.volunteers
          .filter((v) => v.volunteerId !== '')
          .map((v) => ({ id: v.volunteerId as number, additional_info: v.additionalInfo }));
        const mainVol = row.volunteers.find((v) => v.isMain && v.volunteerId !== '');
        return {
          beneficiary: row.beneficiaryId as number,
          volunteers: vols,
          main_volunteer: mainVol ? (mainVol.volunteerId as number) : null,
        };
      });
    saveGroup.mutate(
      { id: selectedGroupId, data: { name: formName, leader: formLeader || null, assignments } },
      {
        onSuccess: (saved) => {
          setPreviousGroupId(null);
          setIsEditing(false);
          if (saved?.id) setSelectedGroupId(saved.id);
        },
      },
    );
  };

  const addVolunteer = (benId: string) =>
    setBenRows((prev) => prev.map((r) => (r.localId === benId ? { ...r, volunteers: [...r.volunteers, emptyVolunteer()] } : r)));

  const removeVolunteer = (benId: string, volId: string) =>
    setBenRows((prev) =>
      prev.map((r) =>
        r.localId === benId
          ? { ...r, volunteers: r.volunteers.length > 1 ? r.volunteers.filter((v) => v.localId !== volId) : r.volunteers }
          : r,
      ),
    );

  const removeBenRow = (benId: string) => setBenRows((prev) => prev.filter((r) => r.localId !== benId));

  const updateVolunteer = (benId: string, volId: string, patch: Partial<VolunteerEntry>) =>
    setBenRows((prev) =>
      prev.map((r) =>
        r.localId === benId ? { ...r, volunteers: r.volunteers.map((v) => (v.localId === volId ? { ...v, ...patch } : v)) } : r,
      ),
    );

  const toggleMain = (benId: string, volId: string) =>
    setBenRows((prev) =>
      prev.map((r) => {
        if (r.localId !== benId) return r;
        const nowMain = !r.volunteers.find((v) => v.localId === volId)?.isMain;
        return { ...r, volunteers: r.volunteers.map((v) => ({ ...v, isMain: v.localId === volId ? nowMain : false })) };
      }),
    );

  const kartyKey = (bId: number, vId: number, month: string) => `${bId}-${vId}-${month}`;
  const showForm = isNewGroup || isEditing;

  const sidebarSlot = (
    <div className="relative">
      <button
        type="button"
        onClick={() => setSidebarDropdownOpen((prev) => !prev)}
        className="flex items-center gap-1 bg-[#3d4558] hover:bg-[#4a5268] text-white text-xs font-bold px-2 py-1 rounded-md transition-colors max-w-[90px]"
      >
        <span className="truncate">{isNewGroup ? '—' : (groups?.find((g) => g.id === selectedGroupId)?.name ?? '—')}</span>
        <span className="shrink-0 opacity-60">▾</span>
      </button>
      {sidebarDropdownOpen && (
        <div
          className="absolute right-0 top-full mt-1 bg-[#2d3345] rounded-xl shadow-2xl z-50 py-1.5 min-w-[140px] border border-white/10"
          onMouseLeave={() => setSidebarDropdownOpen(false)}
        >
          {groups?.map((g) => (
            <button
              key={g.id}
              type="button"
              onClick={() => {
                setSelectedGroupId(g.id);
                setSidebarDropdownOpen(false);
              }}
              className={`w-full text-left px-3 py-1.5 text-xs font-bold transition-colors hover:bg-[#3d4558] ${g.id === selectedGroupId ? 'text-indigo-300' : 'text-white'}`}
            >
              {g.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <PageShell sidebarSlot={sidebarSlot} cardClassName={GROUPS_CARD}>
      {/* ── HEADER ── */}
      <div className="flex items-center justify-between px-6 py-4 border-b shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-2xl">👥</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Grupy</h1>
          {isNewGroup ? (
            <button
              type="button"
              onClick={cancelNewGroup}
              className="px-3 py-1.5 rounded-lg font-bold text-xs border border-gray-200 text-gray-400 hover:bg-gray-50 transition-all"
            >
              Anuluj
            </button>
          ) : (
            <button
              type="button"
              onClick={startNewGroup}
              className="bg-emerald-500 text-white px-3 py-1.5 rounded-lg font-bold text-xs hover:bg-emerald-600 transition-all"
            >
              + Nowa
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!isNewGroup && !isEditing && (
            <button
              type="button"
              onClick={enterEditMode}
              className="px-3 py-2 rounded-lg font-bold text-xs bg-indigo-50 text-indigo-600 hover:bg-indigo-100 transition-all"
            >
              ✏️ Edytuj
            </button>
          )}
          {!isNewGroup && !isEditing && (
            <button
              onClick={() => setShowKartyBO(!showKartyBO)}
              className={`px-3 py-2 rounded-lg font-bold text-xs uppercase transition-all ${showKartyBO ? 'bg-amber-500 text-white shadow-md shadow-amber-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              💳 Karty BO
            </button>
          )}
        </div>
      </div>

      {/* ── VIEW MODE — read-only ── */}
      {!showForm && !showKartyBO && groupDetail && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-2 gap-6 mb-8">
            <div>
              <p className="text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Nazwa Grupy</p>
              <p className="h-10 flex items-center px-4 border border-gray-100 rounded-lg bg-gray-50 font-bold text-sm text-gray-800">{groupDetail.name}</p>
            </div>
            <div>
              <p className="text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Przewodnik</p>
              <p className="h-10 flex items-center px-4 border border-gray-100 rounded-lg bg-gray-50 font-bold text-sm text-gray-800">{groupDetail.leader_name || '—'}</p>
            </div>
          </div>

          <div className="overflow-hidden rounded-xl border border-gray-200">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-[#1e2330] text-white text-[10px] uppercase tracking-widest">
                  <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-[30%]">Podopieczny</th>
                  <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-[30%]">Wolontariusz</th>
                  <th className="px-4 py-3 text-left font-bold">Bieżące informacje</th>
                </tr>
              </thead>
              <tbody>
                {(groupDetail.beneficiaries || []).length === 0 && (
                  <tr>
                    <td colSpan={3} className="p-8 text-center text-gray-300 italic">Brak podopiecznych w tej grupie</td>
                  </tr>
                )}
                {(groupDetail.beneficiaries || []).flatMap((b: GroupBeneficiary) => {
                  const vols = b.volunteers;
                  if (vols.length === 0)
                    return [
                      <tr key={`${b.id}-empty`} className="border-b border-gray-100">
                        <td className="px-4 py-2.5 border-r border-gray-200 font-bold text-indigo-700">
                          <button
                            type="button"
                            onClick={() => setDetailBeneficiary(beneficiaries?.find((fb) => fb.id === b.id) ?? null)}
                            className="hover:underline text-left"
                          >
                            {b.full_name}
                          </button>
                        </td>
                        <td className="px-4 py-2.5 border-r border-gray-100 text-gray-400 italic">—</td>
                        <td className="px-4 py-2.5 text-gray-400">—</td>
                      </tr>,
                    ];
                  return vols.map((v: AssignmentVolunteer, vi: number) => (
                    <tr key={`${b.id}-${v.id}`} className="border-b border-gray-100 hover:bg-indigo-50/20 transition-colors">
                      {vi === 0 && (
                        <td rowSpan={vols.length} className="px-4 py-2.5 border-r border-gray-200 font-bold text-indigo-700 align-middle">
                          <button
                            type="button"
                            onClick={() => setDetailBeneficiary(beneficiaries?.find((fb) => fb.id === b.id) ?? null)}
                            className="hover:underline text-left"
                          >
                            {b.full_name}
                          </button>
                        </td>
                      )}
                      <td className="px-4 py-2.5 border-r border-gray-100">
                        <button
                          type="button"
                          onClick={() => setDetailVolunteer(volunteers?.find((fv) => fv.id === v.id) ?? null)}
                          className={`flex items-center gap-1.5 font-bold hover:underline text-left ${v.is_main ? 'text-amber-700' : 'text-gray-700'}`}
                        >
                          <span>{v.is_main ? '⭐' : '🙋'}</span>
                          <span>{v.full_name}</span>
                        </button>
                      </td>
                      <td className="px-4 py-2.5 text-gray-600">{v.additional_info || '—'}</td>
                    </tr>
                  ));
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── KARTY BO — Excel monthly grid ── */}
      {showKartyBO && !isNewGroup && (
        <div className="flex-1 overflow-auto p-6">
          {boEligibleRows.length === 0 ? (
            <div className="text-center py-16 text-gray-300">
              <div className="text-5xl mb-4">💳</div>
              <p className="font-bold text-lg">Brak podopiecznych z BO = TAK</p>
              <p className="text-sm mt-2">Przypisz podopiecznych z aktywnym BO do tej grupy.</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-gray-200">
              <table className="text-sm border-collapse w-full">
                <thead>
                  <tr className="bg-[#1e2330] text-white text-[10px] uppercase tracking-widest">
                    <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-44">Podopieczny</th>
                    <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-44">Wolontariusz</th>
                    {months.map((m) => (
                      <th key={m.key} className="px-3 py-3 text-center font-bold border-r border-white/10 last:border-0 w-20">{m.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {boEligibleRows.map(({ beneficiary: b, volunteer: v }, i) => {
                    const isFirst = boEligibleRows.findIndex((r) => r.beneficiary.id === b.id) === i;
                    const span = boEligibleRows.filter((r) => r.beneficiary.id === b.id).length;
                    return (
                      <tr key={`${b.id}-${v.id}`} className={`border-b border-gray-100 last:border-0 hover:bg-amber-50/40 transition-colors ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'}`}>
                        {isFirst && (
                          <td className="px-4 py-2.5 border-r border-gray-200 font-bold text-indigo-700 align-middle" rowSpan={span}>
                            <button
                              onClick={() => setDetailBeneficiary(beneficiaries?.find((fb) => fb.id === b.id) ?? null)}
                              className="hover:underline text-left leading-tight"
                            >
                              {b.full_name}
                            </button>
                          </td>
                        )}
                        <td className="px-4 py-2.5 border-r border-gray-200">
                          <button
                            onClick={() => setDetailVolunteer(volunteers?.find((fv) => fv.id === v.id) ?? null)}
                            className={`flex items-center gap-1.5 font-bold hover:underline text-left ${v.is_main ? 'text-amber-700' : 'text-gray-700'}`}
                          >
                            <span>{v.is_main ? '⭐' : '🙋'}</span>
                            <span>{v.full_name}</span>
                          </button>
                        </td>
                        {months.map((m) => {
                          const key = kartyKey(b.id, v.id, m.key);
                          return (
                            <td key={m.key} className="px-3 py-2.5 text-center border-r border-gray-100 last:border-0">
                              <input
                                type="checkbox"
                                checked={kartyBOStatus[key] || false}
                                onChange={() => setKartyBOStatus((prev) => ({ ...prev, [key]: !prev[key] }))}
                                className="w-4 h-4 rounded border-gray-300 cursor-pointer accent-amber-500"
                              />
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── EDIT / CREATE FORM ── */}
      {showForm && (
        <form onSubmit={handleFormSubmit} className="flex flex-col flex-1">
          <div className="flex-1 overflow-y-auto p-6">
            {/* Name + Leader */}
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Nazwa Grupy</label>
                <input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  required
                  placeholder="np. GRUPA A"
                  className="w-full h-10 border border-gray-200 focus:border-indigo-500 px-4 rounded-lg outline-none font-bold text-sm"
                />
              </div>
              <div>
                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Przewodnik</label>
                <select
                  value={formLeader}
                  onChange={(e) => setFormLeader(Number(e.target.value))}
                  className="w-full h-10 border border-gray-200 focus:border-indigo-500 px-4 rounded-lg outline-none font-bold text-sm bg-white"
                >
                  <option value="">— Wybierz —</option>
                  {volunteers?.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.full_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Excel table */}
            <div className="overflow-hidden rounded-xl border border-gray-200">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-[#1e2330] text-white text-[10px] uppercase tracking-widest">
                    <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-[28%]">Podopieczny</th>
                    <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-[28%]">Wolontariusz</th>
                    <th className="px-4 py-3 text-left font-bold border-r border-white/10">Bieżące informacje</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {benRows.length === 0 && (
                    <tr>
                      <td colSpan={4} className="p-6 text-center text-gray-300 italic text-sm">
                        Kliknij „+ Dodaj podopiecznego" aby dodać podopiecznych do grupy
                      </td>
                    </tr>
                  )}
                  {benRows.flatMap((benRow) => {
                    const vols = benRow.volunteers;
                    const rows: React.ReactNode[] = vols.map((vol, vi) => (
                      <tr key={vol.localId} className="border-b border-gray-100 hover:bg-indigo-50/20 group transition-colors">
                        {vi === 0 && (
                          <td rowSpan={vols.length + 1} className="px-2 py-1.5 border-r border-gray-200 align-top">
                            <div className="flex items-start gap-1 pt-0.5">
                              {(() => {
                                const ben = beneficiaries?.find((b) => b.id === benRow.beneficiaryId);
                                return ben ? (
                                  <button
                                    type="button"
                                    onClick={() => setDetailBeneficiary(ben)}
                                    className="flex-1 text-sm font-bold text-indigo-700 hover:underline px-2 py-1 leading-tight text-left"
                                  >
                                    {ben.full_name}
                                  </button>
                                ) : (
                                  <span className="flex-1 text-sm text-gray-300 italic px-2 py-1">— wybierz —</span>
                                );
                              })()}
                              <button
                                type="button"
                                onClick={() => removeBenRow(benRow.localId)}
                                className="shrink-0 text-gray-300 hover:text-rose-500 text-lg font-bold transition-colors leading-none mt-0.5"
                                title="Usuń podopiecznego"
                              >
                                &times;
                              </button>
                            </div>
                          </td>
                        )}
                        <td className="px-2 py-1.5 border-r border-gray-100">
                          <div className="flex items-center gap-1.5">
                            <button
                              type="button"
                              onClick={() => toggleMain(benRow.localId, vol.localId)}
                              className={`shrink-0 w-6 h-6 flex items-center justify-center rounded text-xs transition-all ${vol.isMain ? 'text-amber-500' : 'text-gray-300 hover:text-gray-400'}`}
                            >
                              {vol.isMain ? '⭐' : '☆'}
                            </button>
                            <select
                              value={vol.volunteerId}
                              onChange={(e) => updateVolunteer(benRow.localId, vol.localId, { volunteerId: Number(e.target.value) || '', additionalInfo: '' })}
                              className={`flex-1 h-8 bg-transparent border-0 outline-none text-sm font-bold cursor-pointer hover:bg-white focus:bg-white rounded px-1 focus:border focus:border-indigo-300 ${vol.isMain ? 'text-amber-700' : 'text-gray-700'}`}
                            >
                              <option value="">— wybierz —</option>
                              {volunteers
                                ?.filter((v) => v.id === vol.volunteerId || !vols.some((ve) => ve.localId !== vol.localId && ve.volunteerId === v.id))
                                .map((v) => (
                                  <option key={v.id} value={v.id}>
                                    {v.full_name}
                                  </option>
                                ))}
                            </select>
                            {vol.volunteerId !== '' && (
                              <button
                                type="button"
                                title="Szczegóły wolontariusza"
                                onClick={() => setDetailVolunteer(volunteers?.find((fv) => fv.id === vol.volunteerId) ?? null)}
                                className="shrink-0 text-gray-300 hover:text-indigo-400 text-base leading-none transition-colors"
                              >
                                ℹ
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-2 py-1.5 border-r border-gray-100">
                          <input
                            type="text"
                            placeholder="Bieżące informacje..."
                            value={vol.additionalInfo}
                            onChange={(e) => updateVolunteer(benRow.localId, vol.localId, { additionalInfo: e.target.value })}
                            className="w-full h-8 bg-transparent border-0 outline-none text-sm text-gray-600 placeholder-gray-300 hover:bg-white focus:bg-white rounded px-2 focus:border focus:border-indigo-300"
                          />
                        </td>
                        <td className="px-2 py-1.5 text-center">
                          <button
                            type="button"
                            onClick={() => removeVolunteer(benRow.localId, vol.localId)}
                            className="text-gray-300 hover:text-rose-500 text-lg font-bold transition-colors"
                            title="Usuń wolontariusza"
                          >
                            &times;
                          </button>
                        </td>
                      </tr>
                    ));
                    rows.push(
                      <tr key={`addvol-${benRow.localId}`} className="border-b-2 border-gray-200">
                        <td colSpan={3} className="px-3 py-1">
                          <button
                            type="button"
                            onClick={() => addVolunteer(benRow.localId)}
                            className="text-xs font-bold text-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 px-1.5 py-0.5 rounded transition-all"
                          >
                            + wolontariusz
                          </button>
                        </td>
                      </tr>,
                    );
                    return rows;
                  })}
                </tbody>
              </table>
            </div>

            <div
              className="relative mt-3"
              tabIndex={-1}
              onBlur={(e) => {
                if (!e.currentTarget.contains(e.relatedTarget)) setShowBeneficiaryPicker(false);
              }}
            >
              <button
                type="button"
                onClick={() => {
                  setShowBeneficiaryPicker((prev) => !prev);
                  setBeneficiaryPickerSearch('');
                }}
                className="text-xs font-bold text-indigo-500 hover:text-indigo-700 px-2 py-1 hover:bg-indigo-50 rounded-lg transition-all"
              >
                + Dodaj podopiecznego
              </button>

              {showBeneficiaryPicker &&
                (() => {
                  const alreadyInForm = new Set(benRows.map((r) => r.beneficiaryId));
                  const available = (beneficiaries ?? []).filter(
                    (b) =>
                      (!b.group || b.group === selectedGroupId) &&
                      !alreadyInForm.has(b.id) &&
                      b.full_name.toLowerCase().includes(beneficiaryPickerSearch.toLowerCase()),
                  );
                  return (
                    <div className="absolute left-0 bottom-full mb-1 w-64 bg-white rounded-xl shadow-xl border border-gray-200 z-30 overflow-hidden">
                      <div className="p-2 border-b border-gray-100">
                        <input
                          autoFocus
                          placeholder="Szukaj..."
                          value={beneficiaryPickerSearch}
                          onChange={(e) => setBeneficiaryPickerSearch(e.target.value)}
                          className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-lg outline-none focus:border-indigo-400"
                        />
                      </div>
                      <div className="max-h-52 overflow-y-auto">
                        {available.length === 0 ? (
                          <p className="text-center text-gray-400 text-xs py-4">Brak nieprzypisanych podopiecznych</p>
                        ) : (
                          available.map((b) => (
                            <button
                              key={b.id}
                              type="button"
                              onClick={() => {
                                setBenRows((prev) => [...prev, { localId: newRowId(), beneficiaryId: b.id, volunteers: [emptyVolunteer()] }]);
                                setShowBeneficiaryPicker(false);
                              }}
                              className="w-full text-left px-3 py-2 hover:bg-indigo-50 transition-colors"
                            >
                              <p className="font-bold text-xs text-gray-800">{b.full_name}</p>
                              {b.address && <p className="text-[10px] text-gray-400 truncate">{b.address}</p>}
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  );
                })()}
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t flex items-center justify-between shrink-0">
            <div>
              {!isNewGroup && (
                <button
                  type="button"
                  onClick={handleDeleteGroup}
                  disabled={deleteGroup.isPending}
                  className="px-4 py-2 rounded-lg font-bold text-sm text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-50"
                >
                  🗑️ Usuń Grupę
                </button>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={isNewGroup ? cancelNewGroup : () => setIsEditing(false)}
                className="text-gray-400 font-bold text-sm hover:text-gray-600 transition-colors"
              >
                Anuluj
              </button>
              <button
                type="submit"
                disabled={saveGroup.isPending}
                className="bg-indigo-600 text-white px-10 py-3 rounded-xl font-bold text-sm uppercase hover:bg-indigo-700 shadow-lg shadow-indigo-100 disabled:opacity-60"
              >
                {saveGroup.isPending ? 'Zapisywanie...' : isNewGroup ? 'Utwórz Grupę' : 'Zapisz Konfigurację'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* ── DETAIL MODALS ── */}
      {detailBeneficiary && (
        <DetailModal
          title={detailBeneficiary.full_name}
          tag={{ text: 'Podopieczny', className: 'text-indigo-500' }}
          fields={beneficiaryDetailFields(detailBeneficiary)}
          valueClassName="text-gray-700"
          onClose={() => setDetailBeneficiary(null)}
        />
      )}
      {detailVolunteer && (
        <DetailModal
          title={detailVolunteer.full_name}
          tag={{ text: 'Wolontariusz', className: 'text-emerald-500' }}
          fields={volunteerDetailFields(detailVolunteer)}
          onClose={() => setDetailVolunteer(null)}
        />
      )}
    </PageShell>
  );
};

export default GroupsPage;
