import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import type { DepartmentDetail, DepartmentInput, DepartmentListItem } from '@/types';

interface DepartmentFormModalProps {
  department: DepartmentListItem | DepartmentDetail | null;
  onClose: () => void;
  onSave: (args: { id?: number | null; data: DepartmentInput }) => void;
  isPending: boolean;
}

/** Create/edit form for a department (name, icon, description). */
const DepartmentFormModal = ({ department, onClose, onSave, isPending }: DepartmentFormModalProps) => {
  const [name, setName] = useState(department?.name ?? '');
  const [icon, setIcon] = useState(department?.icon ?? '');
  const [description, setDescription] = useState(department?.description ?? '');

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    onSave({
      id: department?.id ?? null,
      data: { name: name.trim(), icon: icon.trim(), description: description.trim() },
    });
  };

  return (
    <Modal onClose={onClose}>
      <div className="mb-6 flex items-start justify-between gap-4">
        <h2 className="text-xl font-bold text-gray-900">
          {department ? 'Edytuj dział' : 'Nowy dział'}
        </h2>
        <button onClick={onClose} className="text-2xl leading-none text-gray-400 hover:text-gray-600">
          &times;
        </button>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label htmlFor="department-name" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Nazwa *
          </label>
          <input
            id="department-name"
            type="text"
            value={name}
            required
            maxLength={200}
            onChange={(e) => setName(e.target.value)}
            className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
          />
        </div>
        <div>
          <label htmlFor="department-icon" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Ikona (emoji)
          </label>
          <input
            id="department-icon"
            type="text"
            value={icon}
            maxLength={4}
            placeholder="np. 🧹"
            onChange={(e) => setIcon(e.target.value)}
            className="h-10 w-24 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
          />
        </div>
        <div>
          <label htmlFor="department-description" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Opis
          </label>
          <textarea
            id="department-description"
            value={description}
            maxLength={1000}
            onChange={(e) => setDescription(e.target.value)}
            className="min-h-20 w-full resize-y rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
          />
        </div>

        <div className="flex flex-col-reverse gap-2 border-t pt-5 sm:flex-row sm:justify-end sm:gap-3">
          <button type="button" onClick={onClose} className="px-4 py-2 font-bold text-gray-400">
            Anuluj
          </button>
          <button
            type="submit"
            disabled={isPending || !name.trim()}
            className="min-h-10 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white transition-all hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
          >
            {isPending ? 'Zapisywanie...' : 'Zapisz'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default DepartmentFormModal;
