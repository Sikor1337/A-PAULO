import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import { useRoles } from '@/hooks/useRoles';

interface Props {
  onClose: () => void;
}

/** Lets an admin create, rename, and delete the volunteer Role lookup list. */
const RoleManagerModal = ({ onClose }: Props) => {
  const { data: roles, save, remove } = useRoles();
  const [newName, setNewName] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState('');

  const addRole = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    save.mutate({ id: null, data: { name: newName.trim() } });
    setNewName('');
  };

  const startEdit = (id: number, name: string) => {
    setEditingId(id);
    setEditingName(name);
  };

  const saveEdit = () => {
    if (editingId == null || !editingName.trim()) return;
    save.mutate({ id: editingId, data: { name: editingName.trim() } });
    setEditingId(null);
  };

  return (
    <Modal onClose={onClose} closeOnBackdrop={false} maxWidth="max-w-md">
      <h2 className="text-xl font-bold mb-6 text-gray-900">Zarządzaj rolami</h2>

      <div className="space-y-2 mb-4 max-h-64 overflow-y-auto">
        {roles?.length === 0 && <p className="text-sm text-gray-400 italic">Brak ról.</p>}
        {roles?.map((r) => (
          <div key={r.id} className="flex items-center gap-2 border border-gray-100 rounded-lg px-3 py-2">
            {editingId === r.id ? (
              <input
                value={editingName}
                onChange={(e) => setEditingName(e.target.value)}
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && saveEdit()}
                className="flex-1 border border-gray-200 rounded px-2 py-1 text-sm outline-none focus:border-indigo-400"
              />
            ) : (
              <span className="flex-1 text-sm font-medium text-gray-700">{r.name}</span>
            )}
            {editingId === r.id ? (
              <button type="button" onClick={saveEdit} className="text-emerald-600 text-xs font-bold hover:underline">
                Zapisz
              </button>
            ) : (
              <button type="button" onClick={() => startEdit(r.id, r.name)} className="text-indigo-500 text-xs font-bold hover:underline">
                Zmień
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                if (confirm(`Usunąć rolę "${r.name}"?`)) remove.mutate(r.id);
              }}
              className="text-rose-400 hover:text-rose-600 text-lg leading-none"
              title="Usuń rolę"
            >
              &times;
            </button>
          </div>
        ))}
      </div>

      <form onSubmit={addRole} className="flex gap-2">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Nowa rola..."
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-400"
        />
        <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700">
          + Dodaj
        </button>
      </form>

      <div className="flex justify-end pt-6">
        <button type="button" onClick={onClose} className="px-4 py-2 text-gray-400 font-bold hover:text-gray-600">
          Zamknij
        </button>
      </div>
    </Modal>
  );
};

export default RoleManagerModal;
