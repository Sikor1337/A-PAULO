import { useState } from 'react';
import FormModal from '@/components/ui/FormModal';
import { appDialog } from '@/lib/appDialog';
import type {
  DepartmentInventoryItem,
  DepartmentInventoryItemInput,
  Volunteer,
} from '@/types';

interface Props {
  item: DepartmentInventoryItem | null;
  volunteers: Volunteer[];
  isPending: boolean;
  onClose: () => void;
  onSave: (data: DepartmentInventoryItemInput) => void;
}

const today = () => new Date().toISOString().slice(0, 10);

const DepartmentInventoryModal = ({
  item,
  volunteers,
  isPending,
  onClose,
  onSave,
}: Props) => {
  const [name, setName] = useState(item?.name ?? '');
  const [location, setLocation] = useState(item?.location ?? '');
  const [volunteerId, setVolunteerId] = useState<number | ''>(
    item?.borrowed_by_volunteer_id ?? '',
  );
  const [borrowedAt, setBorrowedAt] = useState(item?.borrowed_at ?? '');

  return (
    <FormModal
      title={item ? 'Edytuj przedmiot' : 'Dodaj przedmiot do magazynu'}
      onClose={onClose}
      isPending={isPending}
      submitLabel={item ? 'Zapisz' : 'Dodaj'}
      onSubmit={(event) => {
        event.preventDefault();
        if (!name.trim() || !location.trim()) {
          appDialog.warning('Uzupełnij nazwę przedmiotu i miejsce znajdowania.');
          return;
        }
        if (volunteerId !== '' && !borrowedAt) {
          appDialog.warning('Podaj datę pobrania przedmiotu.');
          return;
        }
        onSave({
          name: name.trim(),
          location: location.trim(),
          borrowed_by_volunteer_id: volunteerId || null,
          borrowed_at: volunteerId ? borrowedAt : null,
        });
      }}
    >
      <label className="block text-sm font-bold text-gray-700">
        Nazwa przedmiotu
        <input
          required
          maxLength={200}
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="mt-1 min-h-11 w-full rounded-lg border px-3 font-normal"
        />
      </label>
      <label className="block text-sm font-bold text-gray-700">
        Miejsce znajdowania
        <input
          required
          maxLength={300}
          value={location}
          onChange={(event) => setLocation(event.target.value)}
          placeholder="np. szafa w sali nr 2"
          className="mt-1 min-h-11 w-full rounded-lg border px-3 font-normal"
        />
      </label>
      <label className="block text-sm font-bold text-gray-700">
        Wolontariusz, który wziął
        <select
          value={volunteerId}
          onChange={(event) => {
            const value = event.target.value ? Number(event.target.value) : '';
            setVolunteerId(value);
            setBorrowedAt(value ? borrowedAt || today() : '');
          }}
          className="mt-1 min-h-11 w-full rounded-lg border px-3 font-normal"
        >
          <option value="">Przedmiot jest w magazynie</option>
          {volunteers.map((volunteer) => (
            <option key={volunteer.id} value={volunteer.id}>
              {volunteer.full_name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm font-bold text-gray-700">
        Data pobrania
        <input
          type="date"
          required={volunteerId !== ''}
          disabled={volunteerId === ''}
          value={borrowedAt}
          onChange={(event) => setBorrowedAt(event.target.value)}
          className="mt-1 min-h-11 w-full rounded-lg border px-3 font-normal disabled:bg-gray-100"
        />
      </label>
    </FormModal>
  );
};

export default DepartmentInventoryModal;
