import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { volunteerService } from '../services/volunteerService';
import { groupService } from '../services/groupService';
import Sidebar from '../components/Sidebar';

type SortKey = 'full_name' | 'email' | 'phone' | 'status';
type SortDir = 'asc' | 'desc';

const VolunteersPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState('');
    const [filterGroup, setFilterGroup] = useState('');
    const [filterStatus, setFilterStatus] = useState<'' | 'Aktywny' | 'Były'>('');
    const [editingVolunteer, setEditingVolunteer] = useState<any>(null);
    const [detailsVolunteer, setDetailsVolunteer] = useState<any>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [sortKey, setSortKey] = useState<SortKey>('full_name');
    const [sortDir, setSortDir] = useState<SortDir>('asc');
    const { data: volunteers, isLoading } = useQuery({
        queryKey: ['volunteers'],
        queryFn: volunteerService.getAll
    });

    const { data: groups } = useQuery({
        queryKey: ['groups'],
        queryFn: groupService.getAll
    });

    const filteredAndSorted = useMemo(() => {
        if (!volunteers) return [];
        const term = searchTerm.toLowerCase();
        let filtered = volunteers.filter((v: any) =>
            (v.full_name || '').toLowerCase().includes(term) ||
            (v.email || '').toLowerCase().includes(term) ||
            (v.phone || '').toLowerCase().includes(term) ||
            (v.status || '').toLowerCase().includes(term)
        );
        if (filterGroup !== '') {
            filtered = filtered.filter((v: any) =>
                v.led_group === filterGroup ||
                (v.assigned_groups || '').split(', ').includes(filterGroup)
            );
        }
        if (filterStatus !== '') filtered = filtered.filter((v: any) => v.status === filterStatus);
        return filtered.sort((a: any, b: any) => {
            const valA = (a[sortKey] || '').toString().toLowerCase();
            const valB = (b[sortKey] || '').toString().toLowerCase();
            return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        });
    }, [volunteers, searchTerm, sortKey, sortDir, filterGroup, filterStatus]);

    const toggleSort = (key: SortKey) => {
        if (sortKey === key) setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('asc'); }
    };

    const sortIcon = (key: SortKey) => sortKey !== key ? ' ↕' : sortDir === 'asc' ? ' ↑' : ' ↓';

    const mutationSave = useMutation({
        mutationFn: (data: any) => editingVolunteer
            ? volunteerService.update(editingVolunteer.id, data)
            : volunteerService.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['volunteers'] });
            setEditingVolunteer(null);
            setIsAdding(false);
            setFormErrors({});
        },
        onError: (err: any) => alert(err?.response?.data ? JSON.stringify(err.response.data) : 'Błąd zapisu.')
    });

    const mutationDelete = useMutation({
        mutationFn: (id: number) => volunteerService.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['volunteers'] }),
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
        if (!data.email) errors.email = 'Email jest wymagany';
        else if (!/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/.test(data.email)) errors.email = 'Niepoprawny format email';

        if (!data.phone) errors.phone = 'Numer telefonu jest wymagany';
        else if (!/^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$/.test(data.phone)) errors.phone = 'Podaj prawidłowy polski numer (np. +48 123 456 789)';

        if (!data.join_date) {
            errors.join_date = 'Data przystąpienia jest wymagana';
        } else {
            const year = String(data.join_date).split('-')[0];
            if (year && year.length > 4) {
                errors.join_date = 'Niepoprawny format roku (maksymalnie 4 cyfry)';
            }
        }

        if (Object.keys(errors).length > 0) {
            setFormErrors(errors);
            return;
        }

        setFormErrors({});
        mutationSave.mutate(data);
    };

    return (
        <div className="flex min-h-screen bg-[#1e2330]">
            <Sidebar />
            <div className="ml-[260px] flex-1 p-6 text-gray-800">
                <div className="bg-white rounded-xl shadow-lg min-h-[calc(100vh-48px)] p-6">
                    <div className="flex items-center justify-between mb-6 border-b pb-4">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">🙋</span>
                            <h1 className="text-xl font-bold text-gray-900 uppercase">Wolontariusze</h1>
                        </div>
                        <div className="flex gap-4">
                            <button onClick={() => { setIsAdding(true); setFormErrors({}); }} className="bg-[#10b981] text-white px-6 py-2 rounded-lg font-bold text-sm hover:opacity-90 transition-all flex items-center gap-2">
                                + Dodaj
                            </button>
                        </div>
                    </div>
                    <div className="mb-4 flex gap-2 items-center">
                        <input type="text" placeholder="Szukaj po nazwisku, emailu, telefonie..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                            className="flex-1 px-4 h-10 border border-gray-200 rounded-lg bg-gray-50 focus:bg-white focus:border-indigo-500 outline-none text-sm font-medium" />
                        <select value={filterGroup} onChange={e => setFilterGroup(e.target.value)}
                            className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[150px]">
                            <option value="">Wszystkie grupy</option>
                            {groups?.map((g: any) => <option key={g.id} value={g.name}>{g.name}</option>)}
                        </select>
                        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value as '' | 'Aktywny' | 'Były')}
                            className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[130px]">
                            <option value="">Wszystkie statusy</option>
                            <option value="Aktywny">Aktywny</option>
                            <option value="Były">Były</option>
                        </select>
                    </div>
                    <div className="overflow-x-auto border rounded-lg">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-[#1e2330] text-white text-xs uppercase font-bold tracking-wider">
                                    <th className="w-[20%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('full_name')}>Imię i nazwisko{sortIcon('full_name')}</th>
                                    <th className="w-[20%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('email')}>Email{sortIcon('email')}</th>
                                    <th className="w-[15%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('phone')}>Tel{sortIcon('phone')}</th>
                                    <th className="w-[15%] p-3 border-r border-gray-700">Grupa</th>
                                    <th className="w-[10%] p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('status')}>Status{sortIcon('status')}</th>
                                    <th className="w-[10%] p-3 text-center min-w-[100px]">Akcje</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {isLoading ? (
                                    <tr><td colSpan={6} className="p-10 text-center text-gray-400">Ładowanie...</td></tr>
                                ) : filteredAndSorted.length === 0 ? (
                                    <tr><td colSpan={6} className="p-10 text-center text-gray-400">Brak wyników</td></tr>
                                ) : filteredAndSorted.map((v: any) => (
                                    <tr key={v.id} className="hover:bg-blue-50 border-b last:border-0 cursor-pointer transition-colors" onClick={() => setDetailsVolunteer(v)}>
                                        <td className="p-3 border-r font-medium text-gray-700">{v.full_name}</td>
                                        <td className="p-3 border-r text-gray-500">{v.email || '—'}</td>
                                        <td className="p-3 border-r text-gray-500">{v.phone || '—'}</td>
                                        <td className="p-3 border-r text-center">
                                            <div className="flex flex-col items-center gap-1">
                                                {v.led_group && <span className="bg-indigo-100 text-indigo-700 text-[10px] px-2 py-0.5 rounded font-bold uppercase" title="Lider Grupy">👑 {v.led_group}</span>}
                                                {v.main_for_beneficiaries && v.main_for_beneficiaries.map((bName: string) => (
                                                    <span key={bName} className="bg-amber-100 text-amber-800 text-[10px] px-2 py-0.5 rounded font-bold uppercase flex items-center gap-0.5" title={`Główny wolontariusz dla: ${bName}`}>
                                                        ⭐ {bName}
                                                    </span>
                                                ))}
                                                {v.assigned_groups && <span className="text-gray-500 text-xs">{v.assigned_groups}</span>}
                                                {!v.led_group && (!v.main_for_beneficiaries || v.main_for_beneficiaries.length === 0) && !v.assigned_groups && <span className="text-gray-400">—</span>}
                                            </div>
                                        </td>
                                        <td className="p-3 border-r">
                                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${v.status === 'Aktywny' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{v.status}</span>
                                        </td>
                                        <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                                            <div className="flex justify-center gap-2">
                                                <button onClick={() => { setEditingVolunteer(v); setFormErrors({}); }} className="bg-[#6366f1] text-white p-1.5 rounded hover:opacity-80">✏️</button>
                                                <button onClick={() => { if (confirm('Usunąć?')) mutationDelete.mutate(v.id) }} className="bg-[#ef4444] text-white p-1.5 rounded hover:opacity-80">🗑️</button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {detailsVolunteer && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setDetailsVolunteer(null)}>
                    <div className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-between items-start mb-6">
                            <h2 className="text-xl font-bold text-gray-900">{detailsVolunteer.full_name}</h2>
                            <button onClick={() => setDetailsVolunteer(null)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
                        </div>
                        <dl className="space-y-3 text-sm">
                            {[
                                ['Email', detailsVolunteer.email],
                                ['Lider Grupy', detailsVolunteer.led_group],
                                ['Członek Grup', detailsVolunteer.assigned_groups],
                                ['Główny wolontariusz dla', detailsVolunteer.main_for_beneficiaries?.join(', ')],
                                ['Telefon', detailsVolunteer.phone],
                                ['Profil społecznościowy', detailsVolunteer.social_link],
                                ['Status', detailsVolunteer.status],
                                ['Data przystąpienia', detailsVolunteer.join_date],
                                ['Notatki', detailsVolunteer.notes],
                                ['Historia', detailsVolunteer.history],
                            ].map(([label, val]) => (
                                <div key={label as string}>
                                    <dt className="text-[10px] font-black uppercase text-gray-400">{label}</dt>
                                    <dd className="text-gray-800 font-bold">{val || '—'}</dd>
                                </div>
                            ))}
                        </dl>
                        <div className="flex justify-end gap-3 pt-6 border-t mt-6">
                            <button onClick={() => { setEditingVolunteer(detailsVolunteer); setDetailsVolunteer(null); setFormErrors({}); }} className="bg-[#6366f1] text-white px-4 py-2 rounded-md font-bold hover:opacity-90">✏️ Edytuj</button>
                            <button onClick={() => setDetailsVolunteer(null)} className="px-4 py-2 text-gray-400 font-bold">Zamknij</button>
                        </div>
                    </div>
                </div>
            )}

            {(editingVolunteer || isAdding) && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
                        <h2 className="text-xl font-bold mb-6">{isAdding ? 'Nowy Wolontariusz' : 'Edycja Danych'}</h2>
                        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Imię i Nazwisko</label>
                                <input
                                    name="full_name"
                                    defaultValue={editingVolunteer?.full_name}
                                    className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.full_name ? 'border-red-500 bg-red-50' : ''}`}
                                />
                                {formErrors.full_name && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.full_name}</p>}
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Email</label>
                                <input
                                    name="email"
                                    type="text"
                                    autoComplete="off"
                                    defaultValue={editingVolunteer?.email}
                                    className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.email ? 'border-red-500 bg-red-50' : ''}`}
                                />
                                {formErrors.email && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.email}</p>}
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Telefon</label>
                                    <input
                                        name="phone"
                                        type="text"
                                        autoComplete="off"
                                        defaultValue={editingVolunteer?.phone}
                                        className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.phone ? 'border-red-500 bg-red-50' : ''}`}
                                        onInput={(e) => {
                                            const target = e.target as HTMLInputElement;
                                            target.value = target.value.replace(/[^0-9+\s\-()]/g, '');
                                        }}
                                    />
                                    {formErrors.phone && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.phone}</p>}
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Status</label>
                                    <select name="status" defaultValue={editingVolunteer?.status || 'Aktywny'} className="w-full border p-2 rounded-md outline-none focus:border-blue-500 bg-white">
                                        <option value="Aktywny">Aktywny</option>
                                        <option value="Były">Były</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Data przystąpienia</label>
                                <input
                                    name="join_date"
                                    type="date"
                                    max="9999-12-31"
                                    defaultValue={editingVolunteer?.join_date}
                                    className={`w-full border p-2 rounded-md outline-none focus:border-blue-500 ${formErrors.join_date ? 'border-red-500 bg-red-50' : ''}`}
                                />
                                {formErrors.join_date && <p className="text-[10px] text-red-500 font-bold mt-1 flex items-center gap-1">⚠️ {formErrors.join_date}</p>}
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Profil społecznościowy (URL)</label>
                                <input name="social_link" type="text" autoComplete="off" defaultValue={editingVolunteer?.social_link} className="w-full border p-2 rounded-md outline-none focus:border-blue-500" />
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Notatki</label>
                                <textarea name="notes" defaultValue={editingVolunteer?.notes} rows={3} className="w-full border p-2 rounded-md outline-none focus:border-blue-500 resize-none" />
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 mb-1">Historia</label>
                                <textarea name="history" defaultValue={editingVolunteer?.history} rows={3} className="w-full border p-2 rounded-md outline-none focus:border-blue-500 resize-none" />
                            </div>
                            <div className="flex justify-end gap-3 pt-6">
                                <button type="button" onClick={() => { setEditingVolunteer(null); setIsAdding(false); setFormErrors({}); }} className="px-4 py-2 text-gray-400 font-bold hover:text-gray-600">Anuluj</button>
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

export default VolunteersPage;
