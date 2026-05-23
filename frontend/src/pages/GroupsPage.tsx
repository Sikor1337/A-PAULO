import { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { groupService } from '../services/groupService';
import { volunteerService } from '../services/volunteerService';
import { beneficiaryService } from '../services/beneficiaryService';
import Sidebar from '../components/Sidebar';

type SortKey = 'name' | 'leader_name' | 'beneficiary_count' | 'volunteer_count';
type SortDir = 'asc' | 'desc';

interface AssignmentRow {
    beneficiaryId: number | '';
    volunteerIds: number[];
}

const GroupsPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState('');
    const [sortKey, setSortKey] = useState<SortKey>('name');
    const [sortDir, setSortDir] = useState<SortDir>('asc');
    const [selectedGroup, setSelectedGroup] = useState<any>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [editingGroup, setEditingGroup] = useState<any>(null);
    
    const [formAssignments, setFormAssignments] = useState<AssignmentRow[]>([]);
    const [formName, setFormName] = useState('');
    const [formLeader, setFormLeader] = useState<number | ''>('');

    const { data: groups, isLoading } = useQuery({ queryKey: ['groups'], queryFn: groupService.getAll });
    const { data: volunteers } = useQuery({ queryKey: ['volunteers'], queryFn: volunteerService.getAll });
    const { data: beneficiaries } = useQuery({ queryKey: ['beneficiaries'], queryFn: beneficiaryService.getAll });

    const { data: groupDetail } = useQuery({
        queryKey: ['group-detail', selectedGroup?.id],
        queryFn: () => groupService.getById(selectedGroup.id),
        enabled: !!selectedGroup,
    });

    useEffect(() => {
        if (editingGroup) {
            setFormName(editingGroup.name);
            setFormLeader(editingGroup.leader || '');
            const rows = (editingGroup.beneficiaries || []).map((b: any) => ({
                beneficiaryId: b.id,
                volunteerIds: b.volunteers?.map((v: any) => v.id) || []
            }));
            setFormAssignments(rows.length > 0 ? rows : [{ beneficiaryId: '', volunteerIds: [] }]);
        } else if (isAdding) {
            setFormName('');
            setFormLeader('');
            setFormAssignments([{ beneficiaryId: '', volunteerIds: [] }]);
        }
    }, [editingGroup, isAdding]);

    const mutationSaveGroup = useMutation({
        mutationFn: (data: any) => editingGroup
            ? groupService.update(editingGroup.id, data)
            : groupService.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['groups'] });
            queryClient.invalidateQueries({ queryKey: ['beneficiaries'] });
            setEditingGroup(null);
            setIsAdding(false);
        },
        onError: (err: any) => alert(err?.response?.data ? JSON.stringify(err.response.data) : 'Błąd zapisu.')
    });

    const mutationDeleteGroup = useMutation({
        mutationFn: (id: number) => groupService.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['groups'] });
            setSelectedGroup(null);
        },
        onError: () => alert('Nie udało się usunąć.')
    });

    const handleFormSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const validAssignments = formAssignments
            .filter(row => row.beneficiaryId !== '')
            .map(row => ({
                beneficiary: row.beneficiaryId,
                volunteers: row.volunteerIds
            }));

        const data = {
            name: formName,
            leader: formLeader || null,
            assignments: validAssignments
        };
        mutationSaveGroup.mutate(data);
    };

    const addAssignmentRow = () => {
        setFormAssignments([...formAssignments, { beneficiaryId: '', volunteerIds: [] }]);
    };

    const removeAssignmentRow = (index: number) => {
        setFormAssignments(formAssignments.filter((_, i) => i !== index));
    };

    const updateRowBeneficiary = (index: number, val: number) => {
        const newRows = [...formAssignments];
        newRows[index].beneficiaryId = val;
        setFormAssignments(newRows);
    };

    const updateRowVolunteers = (index: number, vId: number) => {
        const newRows = [...formAssignments];
        const currentIds = newRows[index].volunteerIds;
        if (currentIds.includes(vId)) {
            newRows[index].volunteerIds = currentIds.filter(id => id !== vId);
        } else {
            newRows[index].volunteerIds = [...currentIds, vId];
        }
        setFormAssignments(newRows);
    };

    const filteredAndSorted = useMemo(() => {
        if (!groups) return [];
        const term = searchTerm.toLowerCase();
        const filtered = groups.filter((g: any) =>
            (g.name || '').toLowerCase().includes(term) ||
            (g.leader_name || '').toLowerCase().includes(term)
        );
        return filtered.sort((a: any, b: any) => {
            const valA = (a[sortKey] ?? '').toString().toLowerCase();
            const valB = (b[sortKey] ?? '').toString().toLowerCase();
            if (sortKey === 'beneficiary_count' || sortKey === 'volunteer_count') {
                return sortDir === 'asc' ? (a[sortKey] || 0) - (b[sortKey] || 0) : (b[sortKey] || 0) - (a[sortKey] || 0);
            }
            return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        });
    }, [groups, searchTerm, sortKey, sortDir]);

    const toggleSort = (key: SortKey) => {
        if (sortKey === key) setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('asc'); }
    };
    const sortIcon = (key: SortKey) => sortKey !== key ? ' ↕' : sortDir === 'asc' ? ' ↑' : ' ↓';

    return (
        <div className="flex min-h-screen bg-[#1e2330]">
            <Sidebar />
            <div className="ml-[260px] flex-1 p-6 text-gray-800">
                <div className="bg-white rounded-xl shadow-lg p-6 min-h-[calc(100vh-48px)]">
                    {/* Consistent Header */}
                    <div className="flex items-center justify-between mb-6 border-b pb-4">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">👥</span>
                            <h1 className="text-xl font-bold text-gray-900 uppercase">Grupy Przewodników</h1>
                        </div>
                        <button onClick={() => { setIsAdding(true); setEditingGroup(null); }} className="bg-[#10b981] text-white px-6 py-2 rounded-lg font-bold text-sm hover:opacity-90">
                            + Nowa Grupa
                        </button>
                    </div>

                    {/* Uniform Search */}
                    <div className="mb-4">
                        <input type="text" placeholder="Szukaj..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full px-4 h-10 border border-gray-200 rounded-lg bg-gray-50 focus:bg-white focus:border-indigo-500 outline-none text-sm font-medium" />
                    </div>

                    <div className="overflow-x-auto border rounded-lg">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-[#1e2330] text-white text-xs uppercase font-bold tracking-wider">
                                    <th className="w-[30%] p-3 border-r border-gray-700 cursor-pointer" onClick={() => toggleSort('name')}>Grupa{sortIcon('name')}</th>
                                    <th className="w-[30%] p-3 border-r border-gray-700 cursor-pointer" onClick={() => toggleSort('leader_name')}>Przewodnik{sortIcon('leader_name')}</th>
                                    <th className="w-[15%] p-3 border-r border-gray-700 text-center cursor-pointer select-none" onClick={() => toggleSort('beneficiary_count')}>Podopieczni{sortIcon('beneficiary_count')}</th>
                                    <th className="w-[15%] p-3 border-r border-gray-700 text-center cursor-pointer select-none" onClick={() => toggleSort('volunteer_count')}>Wolontariusze{sortIcon('volunteer_count')}</th>
                                    <th className="w-[10%] p-3 text-center min-w-[100px]">Akcje</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {filteredAndSorted.map((g: any) => (
                                    <tr key={g.id} className="hover:bg-blue-50 border-b last:border-0 cursor-pointer transition-colors" onClick={() => setSelectedGroup(g)}>
                                        <td className="p-3 border-r font-bold text-gray-800">{g.name}</td>
                                        <td className="p-3 border-r text-gray-500 font-medium">{g.leader_name || '—'}</td>
                                        <td className="p-3 border-r text-center font-bold text-indigo-600">{g.beneficiary_count}</td>
                                        <td className="p-3 border-r text-center font-bold text-emerald-600">{g.volunteer_count}</td>
                                        <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                                            <div className="flex justify-center gap-2">
                                                <button onClick={() => { setEditingGroup(g); setIsAdding(false); }} className="bg-[#6366f1] text-white p-1.5 rounded hover:opacity-80">✏️</button>
                                                <button onClick={() => { if (confirm('Usunąć grupę?')) mutationDeleteGroup.mutate(g.id) }} className="bg-[#ef4444] text-white p-1.5 rounded hover:opacity-80">🗑️</button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* DETAILS MODAL */}
            {selectedGroup && !editingGroup && !isAdding && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setSelectedGroup(null)}>
                    <div className="bg-white rounded-xl p-8 w-full max-w-2xl shadow-2xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-between items-start mb-6 shrink-0 border-b pb-4">
                            <div>
                                <h2 className="text-2xl font-bold uppercase text-gray-900">{selectedGroup.name}</h2>
                                <p className="text-sm font-bold text-indigo-600 mt-1">
                                    Przewodnik: {selectedGroup.leader_name || 'Brak'}
                                </p>
                            </div>
                            <button onClick={() => setSelectedGroup(null)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto pr-2 space-y-6">
                            <div className="flex gap-8 mb-4">
                                <div className="bg-indigo-50 p-4 rounded-xl flex-1 text-center border border-indigo-100">
                                    <p className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">Podopieczni</p>
                                    <p className="text-3xl font-black text-indigo-700">{selectedGroup.beneficiary_count}</p>
                                </div>
                                <div className="bg-emerald-50 p-4 rounded-xl flex-1 text-center border border-emerald-100">
                                    <p className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-1">Wolontariusze</p>
                                    <p className="text-3xl font-black text-emerald-700">{selectedGroup.volunteer_count}</p>
                                </div>
                            </div>

                            <div>
                                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Struktura przypisań</h3>
                                {(!groupDetail?.beneficiaries || groupDetail.beneficiaries.length === 0) ? (
                                    <div className="text-center p-6 bg-gray-50 rounded-xl text-gray-400 font-medium italic border border-gray-100">
                                        Grupa nie ma jeszcze przypisanych podopiecznych.
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {groupDetail.beneficiaries.map((b: any) => (
                                            <div key={b.id} className="bg-white border border-gray-200 p-4 rounded-xl shadow-sm flex flex-col gap-2">
                                                <div className="flex justify-between items-center">
                                                    <div className="font-bold text-gray-800 text-lg">👤 {b.full_name}</div>
                                                </div>
                                                <div className="flex flex-wrap gap-2 mt-2">
                                                    {b.volunteers?.length > 0 ? (
                                                        b.volunteers.map((v: any) => (
                                                            <span key={v.id} className="bg-emerald-100 text-emerald-700 text-xs px-2.5 py-1 rounded-md font-bold flex items-center gap-1 shadow-sm">
                                                                🙋 {v.full_name}
                                                            </span>
                                                        ))
                                                    ) : (
                                                        <span className="text-xs text-gray-400 italic">Brak wolontariuszy</span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 pt-6 border-t mt-6 shrink-0">
                            <button onClick={() => { setEditingGroup(selectedGroup); setSelectedGroup(null); setIsAdding(false); }} className="bg-[#6366f1] text-white px-6 py-2.5 rounded-xl font-bold uppercase text-sm hover:opacity-90 shadow-md">
                                ✏️ Edytuj Grupę
                            </button>
                            <button onClick={() => setSelectedGroup(null)} className="px-6 py-2.5 text-gray-400 font-bold uppercase text-sm hover:text-gray-600">Zamknij</button>
                        </div>
                    </div>
                </div>
            )}

            {/* COMMAND CENTER MODAL - UNIFIED & SCALED UP */}
            {(editingGroup || isAdding) && (
                <div className="fixed inset-0 bg-[#1e2330]/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl p-8 w-full max-w-4xl shadow-2xl max-h-[90vh] overflow-hidden flex flex-col border border-gray-200">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-8 shrink-0">
                            <h2 className="text-2xl font-bold text-gray-900 uppercase">Konfiguracja Grupy</h2>
                            <button onClick={() => { setEditingGroup(null); setIsAdding(false); }} className="w-10 h-10 flex items-center justify-center rounded-lg bg-gray-100 text-gray-400 hover:text-gray-900 transition-all text-2xl">&times;</button>
                        </div>

                        <form onSubmit={handleFormSubmit} className="space-y-8 flex-1 flex flex-col overflow-hidden">
                            <div className="flex-1 overflow-y-auto pr-2">
                                {/* Main Fields - Unified h-10 */}
                                <div className="grid grid-cols-2 gap-8 mb-8">
                                    <div className="space-y-2">
                                        <label className="block text-xs font-bold uppercase text-gray-400 ml-1">Nazwa Grupy</label>
                                        <input value={formName} onChange={e => setFormName(e.target.value)} required placeholder="np. GRUPA A"
                                            className="w-full h-10 border border-gray-200 focus:border-indigo-500 px-4 rounded-lg outline-none font-bold text-sm" />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-xs font-bold uppercase text-gray-400 ml-1">Przewodnik</label>
                                        <select value={formLeader} onChange={e => setFormLeader(Number(e.target.value))} 
                                            className="w-full h-10 border border-gray-200 focus:border-indigo-500 px-4 rounded-lg outline-none font-bold text-sm bg-white">
                                            <option value="">— Wybierz —</option>
                                            {volunteers?.map((v: any) => <option key={v.id} value={v.id}>{v.full_name}</option>)}
                                        </select>
                                    </div>
                                </div>

                                {/* Assignments Section - Unified Layout */}
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center mb-4">
                                        <h3 className="text-base font-bold text-gray-700 uppercase">Struktura Zespołów</h3>
                                        <button type="button" onClick={addAssignmentRow} className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-bold text-xs uppercase hover:opacity-90">
                                            + Dodaj Podopiecznego
                                        </button>
                                    </div>

                                    {/* Table Header for Row */}
                                    <div className="grid grid-cols-[1fr_2fr_48px] gap-6 px-4 text-xs font-bold text-gray-400 uppercase tracking-widest">
                                        <div>Podopieczny</div>
                                        <div>Wolontariusze</div>
                                        <div></div>
                                    </div>
                                    
                                    <div className="space-y-3">
                                        {formAssignments.map((row, index) => (
                                            <div key={index} className="grid grid-cols-[1fr_2fr_48px] gap-6 items-center bg-gray-50 p-3 rounded-xl border border-gray-100 hover:bg-white transition-all">
                                                {/* Col 1: Beneficiary */}
                                                <select 
                                                    value={row.beneficiaryId} 
                                                    onChange={e => updateRowBeneficiary(index, Number(e.target.value))}
                                                    className="w-full h-10 bg-white border border-gray-200 focus:border-indigo-500 px-3 rounded-lg outline-none text-sm font-bold"
                                                >
                                                    <option value="">Wybierz...</option>
                                                    {beneficiaries
                                                        ?.filter((b: any) => {
                                                            const isAvailable = !b.group || b.group === editingGroup?.id || b.id === row.beneficiaryId;
                                                            const isAlreadySelectedInForm = formAssignments.some((r, i) => i !== index && r.beneficiaryId === b.id);
                                                            return isAvailable && !isAlreadySelectedInForm;
                                                        })
                                                        .map((b: any) => <option key={b.id} value={b.id}>{b.full_name}</option>)}
                                                </select>

                                                {/* Col 2: Volunteers */}
                                                <div className="h-10 bg-white border border-gray-200 px-3 rounded-lg flex items-center gap-2 overflow-hidden">
                                                    <div className="flex-1 flex gap-2 items-center overflow-x-auto no-scrollbar py-1">
                                                        {row.volunteerIds.length === 0 && <span className="text-xs text-gray-300 font-medium italic">Brak przypisań</span>}
                                                        {row.volunteerIds.map(vId => {
                                                            const vol = volunteers?.find((v: any) => v.id === vId);
                                                            return (
                                                                <span key={vId} className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-md font-bold whitespace-nowrap flex items-center gap-1">
                                                                    {vol?.full_name}
                                                                    <button type="button" onClick={() => updateRowVolunteers(index, vId)} className="hover:text-indigo-900">×</button>
                                                                </span>
                                                            );
                                                        })}
                                                    </div>
                                                    <select 
                                                        className="w-[100px] h-7 bg-indigo-50 border-none text-xs font-bold text-indigo-600 px-2 rounded-md outline-none cursor-pointer"
                                                        onChange={(e) => {
                                                            const val = Number(e.target.value);
                                                            if (val) {
                                                                updateRowVolunteers(index, val);
                                                                e.target.value = '';
                                                            }
                                                        }}
                                                    >
                                                        <option value="">+ Dodaj</option>
                                                        {volunteers?.filter((v: any) => !row.volunteerIds.includes(v.id)).map((v: any) => (
                                                            <option key={v.id} value={v.id}>{v.full_name}</option>
                                                        ))}
                                                    </select>
                                                </div>

                                                {/* Col 3: Remove */}
                                                <button type="button" onClick={() => removeAssignmentRow(index)} 
                                                    className="w-10 h-10 flex items-center justify-center rounded-lg bg-white text-rose-300 hover:text-rose-600 border border-gray-100 transition-all text-2xl">
                                                    &times;
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="mt-8 pt-6 flex justify-end gap-6 border-t">
                                <button type="button" onClick={() => { setEditingGroup(null); setIsAdding(false); }} 
                                    className="px-6 py-2 text-gray-400 font-bold text-sm uppercase hover:text-gray-600 transition-colors">
                                    Anuluj
                                </button>
                                <button type="submit" disabled={mutationSaveGroup.isPending} 
                                    className="bg-indigo-600 text-white px-10 py-3 rounded-xl font-bold text-sm uppercase hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100">
                                    {mutationSaveGroup.isPending ? 'Zapisywanie...' : 'Zapisz Konfigurację'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GroupsPage;
