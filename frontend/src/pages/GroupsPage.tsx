import { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { groupService } from '../services/groupService';
import { volunteerService } from '../services/volunteerService';
import { beneficiaryService } from '../services/beneficiaryService';
import Sidebar from '../components/Sidebar';

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
const emptyBenRow = (): BeneficiaryRow => ({ localId: newRowId(), beneficiaryId: '', volunteers: [emptyVolunteer()] });

const GroupsPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
    const [previousGroupId, setPreviousGroupId] = useState<number | null>(null);
    const [showKartyBO, setShowKartyBO] = useState(false);

    const [detailBeneficiary, setDetailBeneficiary] = useState<any>(null);
    const [detailVolunteer, setDetailVolunteer] = useState<any>(null);
    const [kartyBOStatus, setKartyBOStatus] = useState<Record<string, boolean>>({});

    const [benRows, setBenRows] = useState<BeneficiaryRow[]>([emptyBenRow()]);
    const [formName, setFormName] = useState('');
    const [formLeader, setFormLeader] = useState<number | ''>('');

    const [showBeneficiaryPicker, setShowBeneficiaryPicker] = useState(false);
    const [beneficiaryPickerSearch, setBeneficiaryPickerSearch] = useState('');

    const { data: groups } = useQuery({ queryKey: ['groups'], queryFn: groupService.getAll });
    const { data: volunteers } = useQuery({ queryKey: ['volunteers'], queryFn: volunteerService.getAll });
    const { data: beneficiaries } = useQuery({ queryKey: ['beneficiaries'], queryFn: beneficiaryService.getAll });

    const { data: groupDetail } = useQuery({
        queryKey: ['group-detail', selectedGroupId],
        queryFn: () => groupService.getById(selectedGroupId!),
        enabled: !!selectedGroupId,
    });

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
            .filter((b: any) => beneficiaries.find((fb: any) => fb.id === b.id)?.bo_enrolled === true)
            .flatMap((b: any) => (b.volunteers || []).map((v: any) => ({ beneficiary: b, volunteer: v })));
    }, [groupDetail, beneficiaries]);

    // Auto-select first group on initial load
    useEffect(() => {
        if (groups?.length && selectedGroupId === null && previousGroupId === null) {
            setSelectedGroupId(groups[0].id);
        }
    }, [groups, selectedGroupId, previousGroupId]);

    // Populate form from groupDetail
    useEffect(() => {
        if (!groupDetail) return;
        setFormName(groupDetail.name);
        setFormLeader(groupDetail.leader || '');
        const rows: BeneficiaryRow[] = (groupDetail.beneficiaries || []).map((b: any) => ({
            localId: newRowId(),
            beneficiaryId: b.id,
            volunteers: b.volunteers?.length
                ? b.volunteers.map((v: any) => ({ localId: newRowId(), volunteerId: v.id, isMain: v.is_main || false, additionalInfo: v.additional_info || '' }))
                : [emptyVolunteer()]
        }));
        setBenRows(rows.length ? rows : [emptyBenRow()]);
    }, [groupDetail]);

    // Clear form for new group
    useEffect(() => {
        if (isNewGroup) {
            setFormName('');
            setFormLeader('');
            setBenRows([emptyBenRow()]);
            setShowKartyBO(false);
        }
    }, [isNewGroup]);

    const startNewGroup = () => {
        setPreviousGroupId(selectedGroupId);
        setSelectedGroupId(null);
    };

    const cancelNewGroup = () => {
        const fallback = previousGroupId ?? groups?.[0]?.id ?? null;
        setSelectedGroupId(fallback);
        setPreviousGroupId(null);
    };

    const mutationSaveGroup = useMutation({
        mutationFn: (data: any) => selectedGroupId
            ? groupService.update(selectedGroupId, data)
            : groupService.create(data),
        onSuccess: (saved: any) => {
            queryClient.invalidateQueries({ queryKey: ['groups'] });
            queryClient.invalidateQueries({ queryKey: ['beneficiaries'] });
            queryClient.invalidateQueries({ queryKey: ['group-detail'] });
            setPreviousGroupId(null);
            if (saved?.id) setSelectedGroupId(saved.id);
        },
        onError: (err: any) => alert(err?.response?.data ? JSON.stringify(err.response.data) : 'Błąd zapisu.')
    });

    const mutationDeleteGroup = useMutation({
        mutationFn: (id: number) => groupService.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['groups'] });
            queryClient.invalidateQueries({ queryKey: ['beneficiaries'] });
            queryClient.invalidateQueries({ queryKey: ['group-detail'] });
            setPreviousGroupId(null);
            setSelectedGroupId(groups?.find((g: any) => g.id !== selectedGroupId)?.id ?? null);
        },
        onError: () => alert('Nie udało się usunąć grupy.')
    });

    const handleDeleteGroup = () => {
        if (selectedGroupId === null) return;
        const name = groups?.find((g: any) => g.id === selectedGroupId)?.name ?? '';
        if (confirm(`Usunąć grupę „${name}"? Podopieczni zostaną odłączeni, a ich przypisania wolontariuszy usunięte.`)) {
            mutationDeleteGroup.mutate(selectedGroupId);
        }
    };

    const handleFormSubmit = (e: React.BaseSyntheticEvent) => {
        e.preventDefault();
        const assignments = benRows
            .filter(row => row.beneficiaryId !== '')
            .map(row => {
                const vols = row.volunteers.filter(v => v.volunteerId !== '').map(v => ({ id: v.volunteerId as number, additional_info: v.additionalInfo }));
                const mainVol = row.volunteers.find(v => v.isMain && v.volunteerId !== '');
                return { beneficiary: row.beneficiaryId as number, volunteers: vols, main_volunteer: mainVol?.volunteerId ?? null };
            });
        mutationSaveGroup.mutate({ name: formName, leader: formLeader || null, assignments });
    };

    const addVolunteer = (benId: string) =>
        setBenRows(prev => prev.map(r => r.localId === benId ? { ...r, volunteers: [...r.volunteers, emptyVolunteer()] } : r));

    const removeVolunteer = (benId: string, volId: string) =>
        setBenRows(prev => prev.map(r => r.localId === benId
            ? { ...r, volunteers: r.volunteers.length > 1 ? r.volunteers.filter(v => v.localId !== volId) : r.volunteers }
            : r));

    const removeBenRow = (benId: string) =>
        setBenRows(prev => prev.filter(r => r.localId !== benId));

    const updateVolunteer = (benId: string, volId: string, patch: Partial<VolunteerEntry>) =>
        setBenRows(prev => prev.map(r => r.localId === benId
            ? { ...r, volunteers: r.volunteers.map(v => v.localId === volId ? { ...v, ...patch } : v) }
            : r));

    const toggleMain = (benId: string, volId: string) =>
        setBenRows(prev => prev.map(r => {
            if (r.localId !== benId) return r;
            const nowMain = !r.volunteers.find(v => v.localId === volId)?.isMain;
            return { ...r, volunteers: r.volunteers.map(v => ({ ...v, isMain: v.localId === volId ? nowMain : false })) };
        }));

    const [sidebarDropdownOpen, setSidebarDropdownOpen] = useState(false);

    const kartyKey = (bId: number, vId: number, month: string) => `${bId}-${vId}-${month}`;

    return (
        <div className="flex min-h-screen bg-[#1e2330]">
            <Sidebar groupsSlot={
                <div className="relative">
                    <button
                        type="button"
                        onClick={() => setSidebarDropdownOpen(prev => !prev)}
                        className="flex items-center gap-1 bg-[#3d4558] hover:bg-[#4a5268] text-white text-xs font-bold px-2 py-1 rounded-md transition-colors max-w-[90px]"
                    >
                        <span className="truncate">
                            {isNewGroup ? '—' : (groups?.find((g: any) => g.id === selectedGroupId)?.name ?? '—')}
                        </span>
                        <span className="shrink-0 opacity-60">▾</span>
                    </button>
                    {sidebarDropdownOpen && (
                        <div
                            className="absolute right-0 top-full mt-1 bg-[#2d3345] rounded-xl shadow-2xl z-50 py-1.5 min-w-[140px] border border-white/10"
                            onMouseLeave={() => setSidebarDropdownOpen(false)}
                        >
                            {groups?.map((g: any) => (
                                <button
                                    key={g.id}
                                    type="button"
                                    onClick={() => { setSelectedGroupId(g.id); setShowKartyBO(false); setSidebarDropdownOpen(false); }}
                                    className={`w-full text-left px-3 py-1.5 text-xs font-bold transition-colors hover:bg-[#3d4558] ${g.id === selectedGroupId ? 'text-indigo-300' : 'text-white'}`}
                                >
                                    {g.name}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            } />

            <div className="ml-[260px] flex-1 p-6 text-gray-800">
                <div className="bg-white rounded-xl shadow-lg min-h-[calc(100vh-48px)] flex flex-col">

                    {/* ── HEADER ── */}
                    <div className="flex items-center justify-between px-6 py-4 border-b shrink-0">
                        {/* LEFT: title + new/cancel */}
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">👥</span>
                            <h1 className="text-xl font-bold text-gray-900 uppercase">Grupy</h1>
                            {isNewGroup ? (
                                <button type="button" onClick={cancelNewGroup}
                                    className="px-3 py-1.5 rounded-lg font-bold text-xs border border-gray-200 text-gray-400 hover:bg-gray-50 transition-all">
                                    Anuluj
                                </button>
                            ) : (
                                <button type="button" onClick={startNewGroup}
                                    className="bg-emerald-500 text-white px-3 py-1.5 rounded-lg font-bold text-xs hover:bg-emerald-600 transition-all">
                                    + Nowa
                                </button>
                            )}
                        </div>

                        {/* RIGHT: Karty BO */}
                        <div>
                            {!isNewGroup && (
                                <button
                                    onClick={() => setShowKartyBO(!showKartyBO)}
                                    className={`px-3 py-2 rounded-lg font-bold text-xs uppercase transition-all ${showKartyBO ? 'bg-amber-500 text-white shadow-md shadow-amber-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                                >💳 Karty BO</button>
                            )}
                        </div>
                    </div>

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
                                                {months.map(m => (
                                                    <th key={m.key} className="px-3 py-3 text-center font-bold border-r border-white/10 last:border-0 w-20">{m.label}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {boEligibleRows.map(({ beneficiary: b, volunteer: v }: any, i: number) => {
                                                const isFirst = boEligibleRows.findIndex((r: any) => r.beneficiary.id === b.id) === i;
                                                const span = boEligibleRows.filter((r: any) => r.beneficiary.id === b.id).length;
                                                return (
                                                    <tr key={`${b.id}-${v.id}`} className={`border-b border-gray-100 last:border-0 hover:bg-amber-50/40 transition-colors ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'}`}>
                                                        {isFirst && (
                                                            <td className="px-4 py-2.5 border-r border-gray-200 font-bold text-indigo-700 align-middle" rowSpan={span}>
                                                                <button
                                                                    onClick={() => setDetailBeneficiary(beneficiaries?.find((fb: any) => fb.id === b.id) || { id: b.id, full_name: b.full_name })}
                                                                    className="hover:underline text-left leading-tight"
                                                                >{b.full_name}</button>
                                                            </td>
                                                        )}
                                                        <td className="px-4 py-2.5 border-r border-gray-200">
                                                            <button
                                                                onClick={() => setDetailVolunteer(volunteers?.find((fv: any) => fv.id === v.id) || { id: v.id, full_name: v.full_name })}
                                                                className={`flex items-center gap-1.5 font-bold hover:underline text-left ${v.is_main ? 'text-amber-700' : 'text-gray-700'}`}
                                                            ><span>{v.is_main ? '⭐' : '🙋'}</span><span>{v.full_name}</span></button>
                                                        </td>
                                                        {months.map(m => {
                                                            const key = kartyKey(b.id, v.id, m.key);
                                                            return (
                                                                <td key={m.key} className="px-3 py-2.5 text-center border-r border-gray-100 last:border-0">
                                                                    <input type="checkbox"
                                                                        checked={kartyBOStatus[key] || false}
                                                                        onChange={() => setKartyBOStatus(prev => ({ ...prev, [key]: !prev[key] }))}
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

                    {/* ── CONFIG FORM — Excel-like table ── */}
                    {!showKartyBO && (
                        <form onSubmit={handleFormSubmit} className="flex flex-col flex-1">
                            <div className="flex-1 overflow-y-auto p-6">

                                {/* Name + Leader */}
                                <div className="grid grid-cols-2 gap-6 mb-8">
                                    <div>
                                        <label className="block text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Nazwa Grupy</label>
                                        <input value={formName} onChange={e => setFormName(e.target.value)} required placeholder="np. GRUPA A"
                                            className="w-full h-10 border border-gray-200 focus:border-indigo-500 px-4 rounded-lg outline-none font-bold text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-black uppercase text-gray-400 mb-1.5 ml-1">Przewodnik</label>
                                        <select value={formLeader} onChange={e => setFormLeader(Number(e.target.value))}
                                            className="w-full h-10 border border-gray-200 focus:border-indigo-500 px-4 rounded-lg outline-none font-bold text-sm bg-white">
                                            <option value="">— Wybierz —</option>
                                            {volunteers?.map((v: any) => <option key={v.id} value={v.id}>{v.full_name}</option>)}
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
                                            {benRows.flatMap(benRow => {
                                                const vols = benRow.volunteers;
                                                const rows: React.ReactNode[] = vols.map((vol, vi) => (
                                                    <tr key={vol.localId} className="border-b border-gray-100 hover:bg-indigo-50/20 group transition-colors">
                                                        {vi === 0 && (
                                                            <td rowSpan={vols.length + 1} className="px-2 py-1.5 border-r border-gray-200 align-top">
                                                                <div className="flex items-start gap-1 pt-0.5">
                                                                    {(() => {
                                                                        const ben = beneficiaries?.find((b: any) => b.id === benRow.beneficiaryId);
                                                                        return ben ? (
                                                                            <button type="button" onClick={() => setDetailBeneficiary(ben)}
                                                                                className="flex-1 text-sm font-bold text-indigo-700 hover:underline px-2 py-1 leading-tight text-left">
                                                                                {ben.full_name}
                                                                            </button>
                                                                        ) : (
                                                                            <span className="flex-1 text-sm text-gray-300 italic px-2 py-1">— wybierz —</span>
                                                                        );
                                                                    })()}
                                                                    <button type="button" onClick={() => removeBenRow(benRow.localId)}
                                                                        className="shrink-0 text-gray-300 hover:text-rose-500 text-lg font-bold transition-colors leading-none mt-0.5" title="Usuń podopiecznego">
                                                                        &times;
                                                                    </button>
                                                                </div>
                                                            </td>
                                                        )}
                                                        <td className="px-2 py-1.5 border-r border-gray-100">
                                                            <div className="flex items-center gap-1.5">
                                                                <button type="button" onClick={() => toggleMain(benRow.localId, vol.localId)}
                                                                    className={`shrink-0 w-6 h-6 flex items-center justify-center rounded text-xs transition-all ${vol.isMain ? 'text-amber-500' : 'text-gray-300 hover:text-gray-400'}`}>
                                                                    {vol.isMain ? '⭐' : '☆'}
                                                                </button>
                                                                <select
                                                                    value={vol.volunteerId}
                                                                    onChange={e => updateVolunteer(benRow.localId, vol.localId, { volunteerId: Number(e.target.value) || '' })}
                                                                    className={`flex-1 h-8 bg-transparent border-0 outline-none text-sm font-bold cursor-pointer hover:bg-white focus:bg-white rounded px-1 focus:border focus:border-indigo-300 ${vol.isMain ? 'text-amber-700' : 'text-gray-700'}`}
                                                                >
                                                                    <option value="">— wybierz —</option>
                                                                    {volunteers
                                                                        ?.filter((v: any) =>
                                                                            v.id === vol.volunteerId ||
                                                                            !vols.some(ve => ve.localId !== vol.localId && ve.volunteerId === v.id)
                                                                        )
                                                                        .map((v: any) => <option key={v.id} value={v.id}>{v.full_name}</option>)}
                                                                </select>
                                                                {vol.volunteerId !== '' && (
                                                                    <button type="button" title="Szczegóły wolontariusza"
                                                                        onClick={() => setDetailVolunteer(volunteers?.find((fv: any) => fv.id === vol.volunteerId) ?? null)}
                                                                        className="shrink-0 text-gray-300 hover:text-indigo-400 text-base leading-none transition-colors">
                                                                        ℹ
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </td>
                                                        <td className="px-2 py-1.5 border-r border-gray-100">
                                                            <input type="text" placeholder="Bieżące informacje..."
                                                                value={vol.additionalInfo}
                                                                onChange={e => updateVolunteer(benRow.localId, vol.localId, { additionalInfo: e.target.value })}
                                                                className="w-full h-8 bg-transparent border-0 outline-none text-sm text-gray-600 placeholder-gray-300 hover:bg-white focus:bg-white rounded px-2 focus:border focus:border-indigo-300"
                                                            />
                                                        </td>
                                                        <td className="px-2 py-1.5 text-center">
                                                            <button type="button" onClick={() => removeVolunteer(benRow.localId, vol.localId)}
                                                                className="text-gray-300 hover:text-rose-500 text-lg font-bold transition-colors" title="Usuń wolontariusza">
                                                                &times;
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ));
                                                rows.push(
                                                    <tr key={`addvol-${benRow.localId}`} className="border-b-2 border-gray-200">
                                                        <td colSpan={3} className="px-3 py-1">
                                                            <button type="button" onClick={() => addVolunteer(benRow.localId)}
                                                                className="text-xs font-bold text-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 px-1.5 py-0.5 rounded transition-all">
                                                                + wolontariusz
                                                            </button>
                                                        </td>
                                                    </tr>
                                                );
                                                return rows;
                                            })}
                                        </tbody>
                                    </table>
                                </div>

                                <div
                                    className="relative mt-3"
                                    tabIndex={-1}
                                    onBlur={e => { if (!e.currentTarget.contains(e.relatedTarget)) setShowBeneficiaryPicker(false); }}
                                >
                                    <button type="button"
                                        onClick={() => { setShowBeneficiaryPicker(prev => !prev); setBeneficiaryPickerSearch(''); }}
                                        className="text-xs font-bold text-indigo-500 hover:text-indigo-700 px-2 py-1 hover:bg-indigo-50 rounded-lg transition-all">
                                        + Dodaj podopiecznego
                                    </button>

                                    {showBeneficiaryPicker && (() => {
                                        const alreadyInForm = new Set(benRows.map(r => r.beneficiaryId));
                                        const available = (beneficiaries ?? []).filter((b: any) =>
                                            (!b.group || b.group === selectedGroupId) &&
                                            !alreadyInForm.has(b.id) &&
                                            b.full_name.toLowerCase().includes(beneficiaryPickerSearch.toLowerCase())
                                        );
                                        return (
                                            <div className="absolute left-0 bottom-full mb-1 w-64 bg-white rounded-xl shadow-xl border border-gray-200 z-30 overflow-hidden">
                                                <div className="p-2 border-b border-gray-100">
                                                    <input
                                                        autoFocus
                                                        placeholder="Szukaj..."
                                                        value={beneficiaryPickerSearch}
                                                        onChange={e => setBeneficiaryPickerSearch(e.target.value)}
                                                        className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-lg outline-none focus:border-indigo-400"
                                                    />
                                                </div>
                                                <div className="max-h-52 overflow-y-auto">
                                                    {available.length === 0 ? (
                                                        <p className="text-center text-gray-400 text-xs py-4">Brak nieprzypisanych podopiecznych</p>
                                                    ) : available.map((b: any) => (
                                                        <button key={b.id} type="button"
                                                            onClick={() => { setBenRows(prev => [...prev, { localId: newRowId(), beneficiaryId: b.id, volunteers: [emptyVolunteer()] }]); setShowBeneficiaryPicker(false); }}
                                                            className="w-full text-left px-3 py-2 hover:bg-indigo-50 transition-colors">
                                                            <p className="font-bold text-xs text-gray-800">{b.full_name}</p>
                                                            {b.address && <p className="text-[10px] text-gray-400 truncate">{b.address}</p>}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })()}
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="px-6 py-4 border-t flex items-center justify-between shrink-0">
                                {isNewGroup ? (
                                    <button type="button" onClick={cancelNewGroup}
                                        className="text-gray-400 font-bold text-sm hover:text-gray-600 transition-colors">
                                        Anuluj
                                    </button>
                                ) : (
                                    <button type="button" onClick={handleDeleteGroup} disabled={mutationDeleteGroup.isPending}
                                        className="px-4 py-2 rounded-lg font-bold text-sm text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-50">
                                        🗑️ Usuń Grupę
                                    </button>
                                )}
                                <button type="submit" disabled={mutationSaveGroup.isPending}
                                    className="bg-indigo-600 text-white px-10 py-3 rounded-xl font-bold text-sm uppercase hover:bg-indigo-700 shadow-lg shadow-indigo-100 disabled:opacity-60">
                                    {mutationSaveGroup.isPending ? 'Zapisywanie...' : (isNewGroup ? 'Utwórz Grupę' : 'Zapisz Konfigurację')}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>

            {/* ── BENEFICIARY DETAIL MODAL ── */}
            {detailBeneficiary && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setDetailBeneficiary(null)}>
                    <div className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <p className="text-[10px] font-bold uppercase text-indigo-500 tracking-wider mb-1">Podopieczny</p>
                                <h2 className="text-xl font-bold text-gray-900">{detailBeneficiary.full_name}</h2>
                            </div>
                            <button onClick={() => setDetailBeneficiary(null)} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
                        </div>
                        <dl className="space-y-3 text-sm">
                            {([
                                ['Adres', detailBeneficiary.address],
                                ['Grupa', detailBeneficiary.group_name],
                                ['Telefon', detailBeneficiary.phone],
                                ['Telefon rodziny', detailBeneficiary.family_phone],
                                ['Status', detailBeneficiary.status],
                                ['BO', detailBeneficiary.bo_enrolled ? 'Tak' : 'Nie'],
                                ['Opis / Notatki', detailBeneficiary.description],
                                ['Ostatnia wizyta księdza', detailBeneficiary.last_priest_visit],
                                ['Ostatnie spotkanie z wol.', detailBeneficiary.last_volunteer_meeting],
                                ['Historia', detailBeneficiary.history],
                            ] as [string, any][]).map(([label, val]) => (
                                <div key={label}>
                                    <dt className="text-[10px] font-black uppercase text-gray-400">{label}</dt>
                                    <dd className="text-gray-700">{val || '—'}</dd>
                                </div>
                            ))}
                        </dl>
                        <div className="flex justify-end pt-6 border-t mt-6">
                            <button onClick={() => setDetailBeneficiary(null)} className="px-4 py-2 text-gray-400 font-bold">Zamknij</button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── VOLUNTEER DETAIL MODAL ── */}
            {detailVolunteer && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setDetailVolunteer(null)}>
                    <div className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <p className="text-[10px] font-bold uppercase text-emerald-500 tracking-wider mb-1">Wolontariusz</p>
                                <h2 className="text-xl font-bold text-gray-900">{detailVolunteer.full_name}</h2>
                            </div>
                            <button onClick={() => setDetailVolunteer(null)} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
                        </div>
                        <dl className="space-y-3 text-sm">
                            {([
                                ['Email', detailVolunteer.email],
                                ['Lider Grupy', detailVolunteer.led_group],
                                ['Członek Grup', detailVolunteer.assigned_groups],
                                ['Główny wolontariusz dla', Array.isArray(detailVolunteer.main_for_beneficiaries) ? detailVolunteer.main_for_beneficiaries.join(', ') : detailVolunteer.main_for_beneficiaries],
                                ['Telefon', detailVolunteer.phone],
                                ['Profil społecznościowy', detailVolunteer.social_link],
                                ['Status', detailVolunteer.status],
                                ['Data przystąpienia', detailVolunteer.join_date],
                                ['Notatki', detailVolunteer.notes],
                                ['Historia', detailVolunteer.history],
                            ] as [string, any][]).map(([label, val]) => (
                                <div key={label}>
                                    <dt className="text-[10px] font-black uppercase text-gray-400">{label}</dt>
                                    <dd className="text-gray-800 font-bold">{val || '—'}</dd>
                                </div>
                            ))}
                        </dl>
                        <div className="flex justify-end pt-6 border-t mt-6">
                            <button onClick={() => setDetailVolunteer(null)} className="px-4 py-2 text-gray-400 font-bold">Zamknij</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GroupsPage;
