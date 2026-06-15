import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { beneficiaryService } from '../services/beneficiaryService';
import { groupService } from '../services/groupService';
import Sidebar from '../components/Sidebar';

type SortKey = 'full_name' | 'address' | 'phone' | 'status' | 'group_name' | 'bo_enrolled';
type SortDir = 'asc' | 'desc';

const BeneficiariesPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState('');
    const [filterGroup, setFilterGroup] = useState<number | ''>('');
    const [filterBO, setFilterBO] = useState<'' | 'yes' | 'no'>('');
    const [editingBeneficiary, setEditingBeneficiary] = useState<any>(null);
    const [detailsBeneficiary, setDetailsBeneficiary] = useState<any>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [sortKey, setSortKey] = useState<SortKey>('full_name');
    const [sortDir, setSortDir] = useState<SortDir>('asc');

    const { data: beneficiaries, isLoading } = useQuery({
        queryKey: ['beneficiaries'],
        queryFn: beneficiaryService.getAll
    });

    const { data: groups } = useQuery({
        queryKey: ['groups'],
        queryFn: groupService.getAll
    });

    const filteredAndSorted = useMemo(() => {
        if (!beneficiaries) return [];
        const term = searchTerm.toLowerCase();
        let filtered = beneficiaries.filter((b: any) =>
            (b.full_name || '').toLowerCase().includes(term) ||
            (b.address || '').toLowerCase().includes(term) ||
            (b.phone || '').toLowerCase().includes(term) ||
            (b.status || '').toLowerCase().includes(term)
        );
        if (filterGroup !== '') filtered = filtered.filter((b: any) => b.group === filterGroup);
        if (filterBO === 'yes') filtered = filtered.filter((b: any) => b.bo_enrolled === true);
        if (filterBO === 'no') filtered = filtered.filter((b: any) => !b.bo_enrolled);
        return filtered.sort((a: any, b: any) => {
            let cmp: number;
            if (sortKey === 'bo_enrolled') {
                cmp = (a.bo_enrolled ? 1 : 0) - (b.bo_enrolled ? 1 : 0);
            } else {
                const valA = (a[sortKey] || '').toString().toLowerCase();
                const valB = (b[sortKey] || '').toString().toLowerCase();
                cmp = valA.localeCompare(valB);
            }
            return sortDir === 'asc' ? cmp : -cmp;
        });
    }, [beneficiaries, searchTerm, sortKey, sortDir, filterGroup, filterBO]);

    const toggleSort = (key: SortKey) => {
        if (sortKey === key) setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('asc'); }
    };

    const sortIcon = (key: SortKey) => sortKey !== key ? ' ↕' : sortDir === 'asc' ? ' ↑' : ' ↓';

    const mutationSave = useMutation({
        mutationFn: (data: any) => editingBeneficiary
            ? beneficiaryService.update(editingBeneficiary.id, data)
            : beneficiaryService.create(data),
        onSuccess: () => { 
            queryClient.invalidateQueries({ queryKey: ['beneficiaries'] }); 
            setEditingBeneficiary(null); 
            setIsAdding(false); 
            setFormErrors({});
        },
        onError: (err: any) => alert(err?.response?.data ? JSON.stringify(err.response.data) : 'Błąd zapisu.')
    });

    const mutationDelete = useMutation({
        mutationFn: (id: number) => beneficiaryService.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['beneficiaries'] }),
        onError: () => alert('Nie udało się usunąć.')
    });

    const [formErrors, setFormErrors] = useState<Record<string, string>>({});

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const fd = new FormData(e.target as HTMLFormElement);
        const data: any = Object.fromEntries(fd.entries());
        
        // Manualna walidacja dla zachowania standardu UI
        const errors: Record<string, string> = {};
        if (!data.full_name) errors.full_name = 'Imię i nazwisko jest wymagane';
        if (!data.address) errors.address = 'Adres jest wymagany';
        if (!data.phone) errors.phone = 'Numer telefonu jest wymagany';
        else if (!/^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$/.test(data.phone)) errors.phone = 'Podaj prawidłowy polski numer (np. +48 123 456 789)';
        
        if (!data.family_phone) errors.family_phone = 'Telefon rodziny jest wymagany';
        else if (!/^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$/.test(data.family_phone)) errors.family_phone = 'Podaj prawidłowy polski numer (np. +48 123 456 789)';

        if (Object.keys(errors).length > 0) {
            setFormErrors(errors);
            return;
        }

        setFormErrors({});
        data.bo_enrolled = fd.get('bo_enrolled') === 'on';
        data.group = data.group ? Number(data.group) : null;
        data.last_priest_visit = data.last_priest_visit || null;
        data.last_volunteer_meeting = data.last_volunteer_meeting || null;
        mutationSave.mutate(data);
    };

    return (
        <div className="flex min-h-screen bg-[#1e2330]">
            <Sidebar />
            <div className="ml-[260px] flex-1 p-6 text-gray-800">
                <div className="bg-white rounded-xl shadow-lg min-h-[calc(100vh-48px)] p-6">
                    <div className="flex items-center justify-between mb-6 border-b pb-4">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">📄</span>
                            <h1 className="text-xl font-bold text-gray-900 uppercase">Podopieczni</h1>
                        </div>
                        <div className="flex gap-4">
                            <button onClick={() => { setIsAdding(true); setFormErrors({}); }} className="bg-[#10b981] text-white px-6 py-2 rounded-lg font-bold text-sm hover:opacity-90 transition-all flex items-center gap-2">
                                + Dodaj
                            </button>
                        </div>
                    </div>
                    <div className="mb-4 flex gap-2 items-center">
                        <input type="text" placeholder="Szukaj po nazwisku, adresie, telefonie..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                            className="flex-1 px-4 h-10 border border-gray-200 rounded-lg bg-gray-50 focus:bg-white focus:border-indigo-500 outline-none text-sm font-medium" />
                        <select value={filterGroup} onChange={e => setFilterGroup(e.target.value === '' ? '' : Number(e.target.value))}
                            className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[150px]">
                            <option value="">Wszystkie grupy</option>
                            {groups?.map((g: any) => <option key={g.id} value={g.id}>{g.name}</option>)}
                        </select>
                        <select value={filterBO} onChange={e => setFilterBO(e.target.value as '' | 'yes' | 'no')}
                            className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[120px]">
                            <option value="">BO: Wszystkie</option>
                            <option value="yes">BO: TAK</option>
                            <option value="no">BO: NIE</option>
                        </select>
                    </div>
                    <div className="overflow-x-auto border rounded-lg">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-[#1e2330] text-white text-xs uppercase font-bold tracking-wider">
                                    <th className="w-[20%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('full_name')}>Imię i nazwisko{sortIcon('full_name')}</th>
                                    <th className="w-[25%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('address')}>Adres{sortIcon('address')}</th>
                                    <th className="w-[15%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('phone')}>Tel{sortIcon('phone')}</th>
                                    <th className="w-[15%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('group_name')}>Grupa{sortIcon('group_name')}</th>
                                    <th className="w-[5%] p-3 border-r border-gray-700 text-center cursor-pointer select-none" onClick={() => toggleSort('bo_enrolled')}>BO{sortIcon('bo_enrolled')}</th>
                                    <th className="w-[10%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('status')}>Status{sortIcon('status')}</th>
                                    <th className="w-[10%] p-3 text-center min-w-[100px]">Akcje</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {isLoading ? (
                                    <tr><td colSpan={7} className="p-10 text-center text-gray-400">Ładowanie...</td></tr>
                                ) : filteredAndSorted.length === 0 ? (
                                    <tr><td colSpan={7} className="p-10 text-center text-gray-400">Brak wyników</td></tr>
                                ) : filteredAndSorted.map((b: any) => (
                                    <tr key={b.id} className="hover:bg-blue-50 border-b last:border-0 transition-colors">
                                        <td className="p-3 border-r font-medium text-indigo-700 cursor-pointer hover:underline" onClick={() => setDetailsBeneficiary(b)}>{b.full_name}</td>
                                        <td className="p-3 border-r text-gray-500">{b.address || '—'}</td>
                                        <td className="p-3 border-r text-gray-500">{b.phone || '—'}</td>
                                        <td className="p-3 border-r text-gray-400 text-center">{b.group_name || '—'}</td>
                                        <td className="p-3 border-r text-center text-xs font-bold">
                                            <span className={b.bo_enrolled ? 'text-green-600' : 'text-gray-400'}>{b.bo_enrolled ? 'TAK' : 'NIE'}</span>
                                        </td>
                                        <td className="p-3 border-r">
                                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${b.status === 'OBECNY' ? 'bg-green-100 text-green-700' : b.status === 'ZMARŁY' ? 'bg-gray-200 text-gray-600' : b.status === 'DPS_ZOL' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>{b.status}</span>
                                        </td>
                                        <td className="p-3 text-center">
                                            <div className="flex justify-center gap-2">
                                                <button onClick={() => { setEditingBeneficiary(b); setFormErrors({}); }} className="bg-[#6366f1] text-white p-1.5 rounded hover:opacity-80">✏️</button>
                                                <button onClick={() => { if (confirm('Usunąć?')) mutationDelete.mutate(b.id) }} className="bg-[#ef4444] text-white p-1.5 rounded hover:opacity-80">🗑️</button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {detailsBeneficiary && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setDetailsBeneficiary(null)}>
                    <div className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-between items-start mb-6">
                            <h2 className="text-xl font-bold text-gray-900">{detailsBeneficiary.full_name}</h2>
                            <button onClick={() => setDetailsBeneficiary(null)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
                        </div>
                        <dl className="space-y-3 text-sm">
                            {[
                                ['Adres', detailsBeneficiary.address],
                                ['Grupa', detailsBeneficiary.group_name],
                                ['Telefon', detailsBeneficiary.phone],
                                ['Telefon rodziny', detailsBeneficiary.family_phone],
                                ['Status', detailsBeneficiary.status],
                                ['BO', detailsBeneficiary.bo_enrolled ? 'Tak' : 'Nie'],
                                ['Opis / Notatki', detailsBeneficiary.description],
                                ['Ostatnia wizyta księdza', detailsBeneficiary.last_priest_visit],
                                ['Ostatnie spotkanie z wol.', detailsBeneficiary.last_volunteer_meeting],
                                ['Historia', detailsBeneficiary.history],
                            ].map(([label, val]) => (
                                <div key={label as string}>
                                    <dt className="text-[10px] font-black uppercase text-gray-400">{label}</dt>
                                    <dd className="text-gray-700">{val || '—'}</dd>
                                </div>
                            ))}
                        </dl>
                        <div className="flex justify-end gap-3 pt-6 border-t mt-6">
                            <button onClick={() => { setEditingBeneficiary(detailsBeneficiary); setDetailsBeneficiary(null); setFormErrors({}); }} className="bg-[#6366f1] text-white px-4 py-2 rounded-md font-bold hover:opacity-90">✏️ Edytuj</button>
                            <button onClick={() => setDetailsBeneficiary(null)} className="px-4 py-2 text-gray-400 font-bold">Zamknij</button>
                        </div>
                    </div>
                </div>
            )}

            {(editingBeneficiary || isAdding) && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
                        <h2 className="text-xl font-bold mb-6">{isAdding ? 'Nowy Podopieczny' : 'Edycja Danych'}</h2>
                        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Imię i Nazwisko</label>
                                <input 
                                    name="full_name" 
                                    defaultValue={editingBeneficiary?.full_name} 
                                    className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.full_name ? 'border-red-500 bg-red-50' : ''}`}
                                />
                                {formErrors.full_name && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.full_name}</p>}
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Adres</label>
                                <input 
                                    name="address" 
                                    type="text"
                                    autoComplete="off"
                                    defaultValue={editingBeneficiary?.address} 
                                    className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.address ? 'border-red-500 bg-red-50' : ''}`} 
                                />
                                {formErrors.address && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.address}</p>}
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Telefon</label>
                                    <input 
                                        name="phone" 
                                        defaultValue={editingBeneficiary?.phone} 
                                        className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.phone ? 'border-red-500 bg-red-50' : ''}`}
                                        onInput={(e) => {
                                            const target = e.target as HTMLInputElement;
                                            target.value = target.value.replace(/[^0-9+\s\-()]/g, '');
                                        }}
                                    />
                                    {formErrors.phone && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.phone}</p>}
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Telefon rodziny</label>
                                    <input 
                                        name="family_phone" 
                                        type="text"
                                        autoComplete="off"
                                        defaultValue={editingBeneficiary?.family_phone} 
                                        className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.family_phone ? 'border-red-500 bg-red-50' : ''}`} 
                                        onInput={(e) => {
                                            const target = e.target as HTMLInputElement;
                                            target.value = target.value.replace(/[^0-9+\s\-()]/g, '');
                                        }}
                                    />
                                    {formErrors.family_phone && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.family_phone}</p>}
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Status</label>
                                    <select name="status" defaultValue={editingBeneficiary?.status || 'OBECNY'} className="w-full border p-2 rounded-md outline-none focus:border-blue-500 bg-white">
                                        <option value="OBECNY">Obecny</option>
                                        <option value="ZMARŁY">Zmarły</option>
                                        <option value="BYŁY">Były</option>
                                        <option value="DPS_ZOL">DPS/ZOL</option>
                                    </select>
                                </div>
                                <div className="flex items-end pb-1">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input type="checkbox" name="bo_enrolled" defaultChecked={editingBeneficiary?.bo_enrolled} className="w-4 h-4 rounded" />
                                        <span className="text-sm font-medium text-gray-600">Objęty BO</span>
                                    </label>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <dt className="text-[10px] font-black uppercase text-gray-400">Grupa</dt>
                                    <dd className="text-gray-700">{editingBeneficiary?.group_name || '—'}</dd>
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Opis / Notatki</label>
                                    <textarea name="description" defaultValue={editingBeneficiary?.description} rows={3} className="w-full border p-2 rounded-md outline-none focus:border-blue-500 resize-none" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Ostatnia wizyta księdza</label>
                                    <input name="last_priest_visit" type="date" max="9999-12-31" defaultValue={editingBeneficiary?.last_priest_visit ?? ''} className="w-full border p-2 rounded-md outline-none focus:border-blue-500" />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Ostatnie spotkanie z wol.</label>
                                    <input name="last_volunteer_meeting" type="date" max="9999-12-31" defaultValue={editingBeneficiary?.last_volunteer_meeting ?? ''} className="w-full border p-2 rounded-md outline-none focus:border-blue-500" />
                                </div>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Historia</label>
                                <textarea name="history" defaultValue={editingBeneficiary?.history} rows={3} className="w-full border p-2 rounded-md outline-none focus:border-blue-500 resize-none" />
                            </div>
                            <div className="flex justify-end gap-3 pt-6">
                                <button type="button" onClick={() => { setEditingBeneficiary(null); setIsAdding(false); setFormErrors({}); }} className="px-4 py-2 text-gray-400 font-bold hover:text-gray-600">Anuluj</button>
                                <button type="submit" disabled={mutationSave.isPending} className="bg-blue-600 text-white px-6 py-2 rounded-md font-bold shadow-md hover:bg-blue-700 disabled:opacity-50">
                                    {mutationSave.isPending ? 'Zapisywanie...' : 'Zatwierdź'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BeneficiariesPage;
