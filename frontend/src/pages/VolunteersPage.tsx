import { useState, useMemo, type FormEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { volunteerService } from '../services/volunteerService';
import Sidebar from '../components/Sidebar';

type SortKey = 'full_name' | 'email' | 'phone' | 'status';
type SortDir = 'asc' | 'desc';

const VolunteersPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState('');
    const [editingVolunteer, setEditingVolunteer] = useState<any>(null);
    const [detailsVolunteer, setDetailsVolunteer] = useState<any>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [sortKey, setSortKey] = useState<SortKey>('full_name');
    const [sortDir, setSortDir] = useState<SortDir>('asc');

    const { data: volunteers, isLoading } = useQuery({
        queryKey: ['volunteers'],
        queryFn: volunteerService.getAll
    });

    const filteredAndSorted = useMemo(() => {
        if (!volunteers) return [];
        const term = searchTerm.toLowerCase();
        const filtered = volunteers.filter((v: any) =>
            (v.full_name || '').toLowerCase().includes(term) ||
            (v.email || '').toLowerCase().includes(term) ||
            (v.phone || '').toLowerCase().includes(term) ||
            (v.status || '').toLowerCase().includes(term)
        );
        return filtered.sort((a: any, b: any) => {
            const valA = (a[sortKey] || '').toString().toLowerCase();
            const valB = (b[sortKey] || '').toString().toLowerCase();
            return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        });
    }, [volunteers, searchTerm, sortKey, sortDir]);

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
        else if (!/[+]?[0-9\s\-()]{7,18}/.test(data.phone)) errors.phone = 'Niepoprawny format telefonu';
        
        if (!data.join_date) errors.join_date = 'Data przystąpienia jest wymagana';

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
            <div className="ml-[260px] flex-1 p-8 text-gray-800">
                <div className="bg-white rounded-xl shadow-lg min-h-[calc(100vh-64px)] p-8">
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl text-purple-500">🙋</span>
                            <h1 className="text-2xl font-semibold">Wolontariusze</h1>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => { setIsAdding(true); setFormErrors({}); }} className="bg-[#10b981] text-white px-4 py-2 rounded-md font-bold hover:opacity-90 transition-all flex items-center gap-2">+ Dodaj</button>
                            <button className="bg-[#3b82f6] text-white px-4 py-2 rounded-md font-bold hover:opacity-90 transition-all flex items-center gap-2">📥 CSV</button>
                        </div>
                    </div>
                    <div className="mb-6">
                        <input type="text" placeholder="Szukaj po nazwisku, emailu, telefonie..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full p-2 border border-gray-200 rounded-md bg-gray-50 focus:outline-none focus:ring-1 focus:ring-blue-400" />
                    </div>
                    <div className="overflow-x-auto border rounded-lg">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-[#1e2330] text-white text-[10px] uppercase font-black">
                                    <th className="p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('full_name')}>Imię{sortIcon('full_name')}</th>
                                    <th className="p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('email')}>Email{sortIcon('email')}</th>
                                    <th className="p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('phone')}>Tel{sortIcon('phone')}</th>
                                    <th className="p-3 border-r border-gray-700">Grupa</th>
                                    <th className="p-3 border-r border-gray-700 cursor-pointer select-none" onClick={() => toggleSort('status')}>Status{sortIcon('status')}</th>
                                    <th className="p-3 border-r border-gray-700">Działy</th>
                                    <th className="p-3 text-center">Akcje</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {isLoading ? (
                                    <tr><td colSpan={7} className="p-10 text-center text-gray-400">Ładowanie...</td></tr>
                                ) : filteredAndSorted.length === 0 ? (
                                    <tr><td colSpan={7} className="p-10 text-center text-gray-400">Brak wyników</td></tr>
                                ) : filteredAndSorted.map((v: any) => (
                                    <tr key={v.id} className="hover:bg-blue-50 border-b last:border-0 cursor-pointer transition-colors" onClick={() => setDetailsVolunteer(v)}>
                                        <td className="p-3 border-r font-medium text-gray-700">{v.full_name}</td>
                                        <td className="p-3 border-r text-gray-500">{v.email || '—'}</td>
                                        <td className="p-3 border-r text-gray-500">{v.phone || '—'}</td>
                                        <td className="p-3 border-r text-gray-400 text-center">—</td>
                                        <td className="p-3 border-r">
                                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${v.status === 'Aktywny' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{v.status}</span>
                                        </td>
                                        <td className="p-3 border-r text-gray-400">—</td>
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
                            <h2 className="text-xl font-bold">{detailsVolunteer.full_name}</h2>
                            <button onClick={() => setDetailsVolunteer(null)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
                        </div>
                        <dl className="space-y-3 text-sm">
                            {[
                                ['Email', detailsVolunteer.email],
                                ['Telefon', detailsVolunteer.phone],
                                ['Profil społecznościowy', detailsVolunteer.social_link],
                                ['Status', detailsVolunteer.status],
                                ['Data przystąpienia', detailsVolunteer.join_date],
                                ['Notatki', detailsVolunteer.notes],
                            ].map(([label, val]) => (
                                <div key={label as string}>
                                    <dt className="text-[10px] font-black uppercase text-gray-400">{label}</dt>
                                    <dd className="text-gray-700">{val || '—'}</dd>
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
