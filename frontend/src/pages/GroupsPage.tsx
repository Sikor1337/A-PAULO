import { useState, useMemo } from 'react';
import PageShell from '@/components/layout/PageShell';
import DetailModal from '@/components/ui/DetailModal';
import { useGroups, useGroupDetail } from '@/hooks/useGroups';
import { useVolunteerList } from '@/hooks/useVolunteers';
import { useBeneficiaryList } from '@/hooks/useBeneficiaries';
import { useBOCardAttachmentActions, useBOCardAttachments } from '@/hooks/useAttachments';
import { attachmentService, BO_CARD_ACCEPT, BO_CARD_MAX_SIZE_BYTES, BO_CARD_SUPPORTED_LABEL } from '@/services/attachmentService';
import { volunteerDetailFields } from '@/features/volunteers/volunteerDetail';
import { beneficiaryDetailFields } from '@/features/beneficiaries/beneficiaryDetail';
import type {
  Volunteer,
  Beneficiary,
  GroupDetail,
  GroupBeneficiary,
  AssignmentVolunteer,
  AssignmentInput,
  BOCardAttachment,
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
const boCardKey = (beneficiaryId: number, volunteerId: number, period: string) => `${beneficiaryId}-${volunteerId}-${period}`;

/** Builds the editable beneficiary/volunteer rows from a loaded group detail. */
const buildRowsFromDetail = (detail: GroupDetail): BeneficiaryRow[] =>
  (detail.beneficiaries || []).map((b) => ({
    localId: newRowId(),
    beneficiaryId: b.id,
    volunteers: b.volunteers.length
      ? b.volunteers.map((v) => ({ localId: newRowId(), volunteerId: v.id, isMain: v.is_main, additionalInfo: v.additional_info }))
      : [emptyVolunteer()],
  }));

const GROUPS_CARD =
  'flex min-h-[calc(100dvh-88px)] flex-col overflow-hidden rounded-xl bg-white shadow-lg lg:min-h-[calc(100dvh-48px)]';
const formatAttachmentSize = (sizeBytes: number) => {
  if (sizeBytes < 1024 * 1024) return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
};

const GroupsPage: React.FC = () => {
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [previousGroupId, setPreviousGroupId] = useState<number | null>(null);
  const [showKartyBO, setShowKartyBO] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const [detailBeneficiary, setDetailBeneficiary] = useState<Beneficiary | null>(null);
  const [detailVolunteer, setDetailVolunteer] = useState<Volunteer | null>(null);

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
  const { data: boCardAttachments = [], isFetching: isFetchingBOCards } = useBOCardAttachments(selectedGroupId, showKartyBO);
  const { uploadBOCard, updateAttachment, deleteAttachment } = useBOCardAttachmentActions(selectedGroupId);

  const isNewGroup = selectedGroupId === null;

  const months = useMemo(() => {
    const now = new Date();
    return Array.from({ length: 6 }, (_, i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - (5 - i), 1);
      return { key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`, label: `${MONTHS_PL[d.getMonth()]} ${String(d.getFullYear()).slice(2)}` };
    });
  }, []);

  const boEligibleRows = useMemo(() => {
    if (!groupDetail?.beneficiaries || !beneficiaries) return [];
    return groupDetail.beneficiaries
      .filter((b) => beneficiaries.find((fb) => fb.id === b.id)?.bo_enrolled === true)
      .flatMap((b) => b.volunteers.map((v) => ({ beneficiary: b, volunteer: v })));
  }, [groupDetail, beneficiaries]);

  const boCardAttachmentsByCell = useMemo(() => {
    const map = new Map<string, BOCardAttachment[]>();
    boCardAttachments.forEach((attachment) => {
      if (!attachment.beneficiary_id || !attachment.volunteer_id || !attachment.period) return;
      const key = boCardKey(attachment.beneficiary_id, attachment.volunteer_id, attachment.period);
      map.set(key, [...(map.get(key) ?? []), attachment]);
    });
    return map;
  }, [boCardAttachments]);

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
    setShowKartyBO(false);
    setIsEditing(false);
    setSelectedGroupId(null);
  };

  const cancelNewGroup = () => {
    setShowKartyBO(false);
    setIsEditing(false);
    setSelectedGroupId(previousGroupId ?? groups?.[0]?.id ?? null);
    setPreviousGroupId(null);
  };

  const enterEditMode = () => {
    if (groupDetail) {
      setFormName(groupDetail.name);
      setFormLeader(groupDetail.leader || '');
      setBenRows(buildRowsFromDetail(groupDetail));
    }
    setShowKartyBO(false);
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
          setShowKartyBO(false);
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
          setShowKartyBO(false);
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

  const showForm = isNewGroup || isEditing;
  const showCardsView = showKartyBO && !showForm && !isNewGroup;
  const attachmentActionsDisabled = uploadBOCard.isPending || updateAttachment.isPending || deleteAttachment.isPending;

  const handleBOCardSelected = (
    files: FileList | null,
    beneficiary: GroupBeneficiary,
    volunteer: AssignmentVolunteer,
    period: string,
  ) => {
    const file = files?.item(0);
    if (!file || selectedGroupId === null) return;
    if (file.size > BO_CARD_MAX_SIZE_BYTES) {
      alert('Plik jest za duży. Maksymalny rozmiar to 10 MB.');
      return;
    }
    uploadBOCard.mutate({
      groupId: selectedGroupId,
      beneficiaryId: beneficiary.id,
      volunteerId: volunteer.id,
      period,
      file,
    });
  };

  const handleViewAttachment = async (attachment: BOCardAttachment) => {
    try {
      await attachmentService.openContent(attachment);
    } catch {
      alert('Nie udało się otworzyć pliku.');
    }
  };

  const handleRenameAttachment = (attachment: BOCardAttachment) => {
    const nextName = prompt('Nazwa pliku', attachment.display_name)?.trim();
    if (!nextName || nextName === attachment.display_name) return;
    updateAttachment.mutate({ id: attachment.id, data: { display_name: nextName } });
  };

  const handleDeleteAttachment = (attachment: BOCardAttachment) => {
    if (!confirm(`Usunąć plik „${attachment.display_name}”?`)) return;
    deleteAttachment.mutate(attachment.id);
  };

  const renderBOCardCell = (
    beneficiary: GroupBeneficiary,
    volunteer: AssignmentVolunteer,
    month: { key: string; label: string },
  ) => {
    const key = boCardKey(beneficiary.id, volunteer.id, month.key);
    const attachments = boCardAttachmentsByCell.get(key) ?? [];
    const fileInputId = `bo-file-${beneficiary.id}-${volunteer.id}-${month.key}`;
    const cameraInputId = `bo-camera-${beneficiary.id}-${volunteer.id}-${month.key}`;

    return (
      <div
        className={`flex min-h-[132px] flex-col gap-2 rounded-lg border px-2.5 py-2 text-left ${
          attachments.length ? 'border-emerald-200 bg-emerald-50/60' : 'border-dashed border-gray-200 bg-gray-50/70'
        }`}
      >
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-black uppercase text-gray-400">{attachments.length ? `${attachments.length} plik` : 'Brak pliku'}</span>
          {isFetchingBOCards && <span className="h-2 w-2 rounded-full bg-amber-400" title="Odświeżanie" />}
        </div>

        <div className="max-h-44 min-h-8 space-y-1.5 overflow-y-auto pr-1">
          {attachments.map((attachment) => (
            <div key={attachment.id} className="rounded-md border border-white/70 bg-white px-2 py-1.5 shadow-sm">
              <p className="truncate text-xs font-bold text-gray-800" title={attachment.display_name}>
                {attachment.display_name}
              </p>
              <p className="text-[10px] text-gray-400">{formatAttachmentSize(attachment.size_bytes)}</p>
              <div className="mt-1 flex flex-wrap gap-1">
                <button
                  type="button"
                  onClick={() => handleViewAttachment(attachment)}
                  className="rounded bg-indigo-50 px-1.5 py-0.5 text-[10px] font-bold text-indigo-600 hover:bg-indigo-100"
                >
                  Podgląd
                </button>
                <button
                  type="button"
                  disabled={attachmentActionsDisabled}
                  onClick={() => handleRenameAttachment(attachment)}
                  className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-bold text-gray-600 hover:bg-gray-200 disabled:opacity-50"
                >
                  Zmień
                </button>
                <button
                  type="button"
                  disabled={attachmentActionsDisabled}
                  onClick={() => handleDeleteAttachment(attachment)}
                  className="rounded bg-rose-50 px-1.5 py-0.5 text-[10px] font-bold text-rose-600 hover:bg-rose-100 disabled:opacity-50"
                >
                  Usuń
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-auto grid grid-cols-2 gap-1.5">
          <input
            id={fileInputId}
            type="file"
            accept={BO_CARD_ACCEPT}
            disabled={uploadBOCard.isPending}
            onChange={(e) => {
              handleBOCardSelected(e.currentTarget.files, beneficiary, volunteer, month.key);
              e.currentTarget.value = '';
            }}
            className="hidden"
          />
          <label
            htmlFor={fileInputId}
            className={`flex min-h-8 cursor-pointer items-center justify-center rounded-md px-2 text-[10px] font-black uppercase ${
              uploadBOCard.isPending ? 'bg-gray-100 text-gray-300' : 'bg-amber-500 text-white hover:bg-amber-600'
            }`}
          >
            Plik
          </label>

          <input
            id={cameraInputId}
            type="file"
            accept="image/*"
            capture="environment"
            disabled={uploadBOCard.isPending}
            onChange={(e) => {
              handleBOCardSelected(e.currentTarget.files, beneficiary, volunteer, month.key);
              e.currentTarget.value = '';
            }}
            className="hidden"
          />
          <label
            htmlFor={cameraInputId}
            className={`flex min-h-8 cursor-pointer items-center justify-center rounded-md px-2 text-[10px] font-black uppercase ${
              uploadBOCard.isPending ? 'bg-gray-100 text-gray-300' : 'bg-gray-900 text-white hover:bg-gray-800'
            }`}
          >
            Aparat
          </label>
        </div>
        <p className="text-[10px] leading-tight text-gray-400">{BO_CARD_SUPPORTED_LABEL}</p>
      </div>
    );
  };

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
      <div className="flex shrink-0 flex-col gap-3 border-b px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-2xl">👥</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Grupy</h1>
          {isNewGroup ? (
            <button
              type="button"
              onClick={cancelNewGroup}
              className="min-h-9 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-bold text-gray-400 transition-all hover:bg-gray-50"
            >
              Anuluj
            </button>
          ) : (
            <button
              type="button"
              onClick={startNewGroup}
              className="min-h-9 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-white transition-all hover:bg-emerald-600"
            >
              + Nowa
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2 sm:flex sm:items-center">
          {!isNewGroup && !isEditing && (
            <button
              type="button"
              onClick={enterEditMode}
              className="min-h-9 rounded-lg bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-600 transition-all hover:bg-indigo-100"
            >
              ✏️ Edytuj
            </button>
          )}
          {!isNewGroup && !isEditing && (
            <button
              onClick={() => setShowKartyBO((prev) => !prev)}
              className={`min-h-9 rounded-lg px-3 py-2 text-xs font-bold uppercase transition-all ${showKartyBO ? 'bg-amber-500 text-white shadow-md shadow-amber-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              {showKartyBO ? '↩ Widok grupy' : '💳 Karty BO'}
            </button>
          )}
        </div>
      </div>

      {/* ── VIEW MODE — read-only ── */}
      {!showForm && !showCardsView && groupDetail && (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          <div className="mb-6 grid grid-cols-1 gap-4 sm:mb-8 sm:grid-cols-2 sm:gap-6">
            <div>
              <p className="text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Nazwa Grupy</p>
              <p className="h-10 flex items-center px-4 border border-gray-100 rounded-lg bg-gray-50 font-bold text-sm text-gray-800">{groupDetail.name}</p>
            </div>
            <div>
              <p className="text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Przewodnik</p>
              <p className="h-10 flex items-center px-4 border border-gray-100 rounded-lg bg-gray-50 font-bold text-sm text-gray-800">{groupDetail.leader_name || '—'}</p>
            </div>
          </div>

          <div className="space-y-3 md:hidden">
            {(groupDetail.beneficiaries || []).length === 0 ? (
              <div className="rounded-lg border border-gray-200 p-8 text-center text-sm italic text-gray-300">
                Brak podopiecznych w tej grupie
              </div>
            ) : (
              (groupDetail.beneficiaries || []).map((b: GroupBeneficiary) => (
                <article key={b.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                  <button
                    type="button"
                    onClick={() => setDetailBeneficiary(beneficiaries?.find((fb) => fb.id === b.id) ?? null)}
                    className="mb-3 text-left text-sm font-bold text-indigo-700 hover:underline"
                  >
                    {b.full_name}
                  </button>

                  {b.volunteers.length === 0 ? (
                    <p className="rounded-md bg-gray-50 px-3 py-2 text-sm italic text-gray-400">Brak wolontariusza</p>
                  ) : (
                    <div className="space-y-3">
                      {b.volunteers.map((v: AssignmentVolunteer) => (
                        <div key={v.id} className="rounded-md bg-gray-50 p-3">
                          <button
                            type="button"
                            onClick={() => setDetailVolunteer(volunteers?.find((fv) => fv.id === v.id) ?? null)}
                            className={`text-left text-sm font-bold hover:underline ${v.is_main ? 'text-amber-700' : 'text-gray-700'}`}
                          >
                            {v.is_main ? 'Główny: ' : ''}
                            {v.full_name}
                          </button>
                          <p className="mt-2 text-xs font-black uppercase text-gray-400">Bieżące informacje</p>
                          <p className="text-sm text-gray-600">{v.additional_info || '-'}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              ))
            )}
          </div>

          <div className="hidden overflow-x-auto rounded-xl border border-gray-200 md:block">
            <table className="w-full min-w-[720px] text-sm border-collapse">
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
      {showCardsView && (
        <div className="flex-1 overflow-auto p-4 sm:p-6">
          <div className="mb-4">
            <p className="text-[10px] font-black uppercase text-gray-400 mb-1">Karty BO</p>
            <h2 className="text-base font-bold text-gray-900">{groupDetail?.name ?? 'Grupa'}</h2>
          </div>
          {boEligibleRows.length === 0 ? (
            <div className="text-center py-16 text-gray-300">
              <div className="text-5xl mb-4">💳</div>
              <p className="font-bold text-lg">Brak podopiecznych z BO = TAK</p>
              <p className="text-sm mt-2">Przypisz podopiecznych z aktywnym BO do tej grupy.</p>
            </div>
          ) : (
            <>
              <div className="space-y-3 md:hidden">
                {boEligibleRows.map(({ beneficiary: b, volunteer: v }) => (
                  <article key={`${b.id}-${v.id}`} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                    <div className="mb-3">
                      <button
                        type="button"
                        onClick={() => setDetailBeneficiary(beneficiaries?.find((fb) => fb.id === b.id) ?? null)}
                        className="text-left text-sm font-bold text-indigo-700 hover:underline"
                      >
                        {b.full_name}
                      </button>
                      <button
                        type="button"
                        onClick={() => setDetailVolunteer(volunteers?.find((fv) => fv.id === v.id) ?? null)}
                        className={`mt-1 block text-left text-sm font-bold hover:underline ${v.is_main ? 'text-amber-700' : 'text-gray-700'}`}
                      >
                        {v.is_main ? 'Główny: ' : ''}
                        {v.full_name}
                      </button>
                    </div>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      {months.map((m) => (
                        <div key={m.key}>
                          <p className="mb-1 text-[10px] font-black uppercase text-gray-400">{m.label}</p>
                          {renderBOCardCell(b, v, m)}
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>

              <div className="hidden overflow-x-auto rounded-xl border border-gray-200 md:block">
                <table className="text-sm border-collapse w-full min-w-[1320px]">
                <thead>
                  <tr className="bg-[#1e2330] text-white text-[10px] uppercase tracking-widest">
                    <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-44">Podopieczny</th>
                    <th className="px-4 py-3 text-left font-bold border-r border-white/10 w-44">Wolontariusz</th>
                    {months.map((m) => (
                      <th key={m.key} className="px-3 py-3 text-center font-bold border-r border-white/10 last:border-0 w-40">{m.label}</th>
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
                          return (
                            <td key={m.key} className="px-2 py-2 align-top border-r border-gray-100 last:border-0">
                              {renderBOCardCell(b, v, m)}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── EDIT / CREATE FORM ── */}
      {showForm && (
        <form onSubmit={handleFormSubmit} className="flex flex-1 flex-col">
          <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            {/* Name + Leader */}
            <div className="mb-6 grid grid-cols-1 gap-4 sm:mb-8 sm:grid-cols-2 sm:gap-6">
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
            <div className="space-y-3 md:hidden">
              {benRows.length === 0 ? (
                <div className="rounded-lg border border-gray-200 p-6 text-center text-sm italic text-gray-300">
                  Kliknij "+ Dodaj podopiecznego" aby dodać podopiecznych do grupy
                </div>
              ) : (
                benRows.map((benRow) => {
                  const vols = benRow.volunteers;
                  const ben = beneficiaries?.find((b) => b.id === benRow.beneficiaryId);

                  return (
                    <article key={benRow.localId} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                      <div className="mb-3 flex items-start gap-3">
                        {ben ? (
                          <button
                            type="button"
                            onClick={() => setDetailBeneficiary(ben)}
                            className="min-w-0 flex-1 text-left text-sm font-bold leading-tight text-indigo-700 hover:underline"
                          >
                            {ben.full_name}
                          </button>
                        ) : (
                          <span className="min-w-0 flex-1 text-sm italic text-gray-300">— wybierz —</span>
                        )}
                        <button
                          type="button"
                          onClick={() => removeBenRow(benRow.localId)}
                          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-xl font-bold leading-none text-gray-300 transition-colors hover:bg-rose-50 hover:text-rose-500"
                          title="Usuń podopiecznego"
                        >
                          &times;
                        </button>
                      </div>

                      <div className="space-y-3">
                        {vols.map((vol) => (
                          <div key={vol.localId} className="rounded-md bg-gray-50 p-3">
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => toggleMain(benRow.localId, vol.localId)}
                                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded text-xs transition-all ${vol.isMain ? 'text-amber-500' : 'text-gray-300 hover:text-gray-400'}`}
                              >
                                {vol.isMain ? '*' : '+'}
                              </button>
                              <select
                                value={vol.volunteerId}
                                onChange={(e) => updateVolunteer(benRow.localId, vol.localId, { volunteerId: Number(e.target.value) || '', additionalInfo: '' })}
                                className={`min-h-10 min-w-0 flex-1 rounded-md border border-gray-200 bg-white px-2 text-sm font-bold outline-none focus:border-indigo-300 ${vol.isMain ? 'text-amber-700' : 'text-gray-700'}`}
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
                                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-sm font-bold text-gray-400 transition-colors hover:bg-indigo-50 hover:text-indigo-500"
                                >
                                  i
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => removeVolunteer(benRow.localId, vol.localId)}
                                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-xl font-bold leading-none text-gray-300 transition-colors hover:bg-rose-50 hover:text-rose-500"
                                title="Usuń wolontariusza"
                              >
                                &times;
                              </button>
                            </div>
                            <input
                              type="text"
                              placeholder="Bieżące informacje..."
                              value={vol.additionalInfo}
                              onChange={(e) => updateVolunteer(benRow.localId, vol.localId, { additionalInfo: e.target.value })}
                              className="mt-2 min-h-10 w-full rounded-md border border-gray-200 bg-white px-3 text-sm text-gray-600 outline-none placeholder:text-gray-300 focus:border-indigo-300"
                            />
                          </div>
                        ))}
                      </div>

                      <button
                        type="button"
                        onClick={() => addVolunteer(benRow.localId)}
                        className="mt-3 min-h-9 rounded-lg px-2 text-xs font-bold text-indigo-500 transition-all hover:bg-indigo-50 hover:text-indigo-700"
                      >
                        + wolontariusz
                      </button>
                    </article>
                  );
                })
              )}
            </div>

            <div className="hidden overflow-x-auto rounded-xl border border-gray-200 md:block">
              <table className="w-full min-w-[820px] text-sm border-collapse">
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
                className="min-h-9 rounded-lg px-2 py-1 text-xs font-bold text-indigo-500 transition-all hover:bg-indigo-50 hover:text-indigo-700"
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
                    <div className="absolute bottom-full left-0 right-0 z-30 mb-1 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl sm:right-auto sm:w-64">
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
          <div className="flex shrink-0 flex-col gap-3 border-t px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div>
              {!isNewGroup && (
                <button
                  type="button"
                  onClick={handleDeleteGroup}
                  disabled={deleteGroup.isPending}
                  className="min-h-10 rounded-lg px-4 py-2 text-sm font-bold text-rose-600 transition-colors hover:bg-rose-50 disabled:opacity-50"
                >
                  🗑️ Usuń Grupę
                </button>
              )}
            </div>
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:gap-3">
              <button
                type="button"
                onClick={isNewGroup ? cancelNewGroup : () => {
                  setIsEditing(false);
                  setShowKartyBO(false);
                }}
                className="min-h-10 px-3 text-sm font-bold text-gray-400 transition-colors hover:text-gray-600"
              >
                Anuluj
              </button>
              <button
                type="submit"
                disabled={saveGroup.isPending}
                className="min-h-11 rounded-lg bg-indigo-600 px-6 py-3 text-sm font-bold uppercase text-white shadow-lg shadow-indigo-100 hover:bg-indigo-700 disabled:opacity-60 sm:px-10"
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
