import { useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import FormModal from '@/components/ui/FormModal';
import { Field, TextInput, SelectInput, TextArea } from '@/components/ui/form';
import { rules, sanitizePhoneInput } from '@/lib/validation';
import { toDateInputValue } from '@/lib/date';
import { useFunctions } from '@/hooks/useFunctions';
import type { Volunteer, VolunteerInput } from '@/types';

interface Props {
  /** Volunteer being edited, or null when adding a new one. */
  volunteer: Volunteer | null;
  onClose: () => void;
  onSave: (args: { id: number | null; data: VolunteerInput }) => void;
  isPending: boolean;
}

function defaults(v: Volunteer | null): VolunteerInput {
  return {
    full_name: v?.full_name ?? '',
    email: v?.email ?? '',
    phone: v?.phone ?? '',
    status: v?.status ?? 'Aktywny',
    function_ids: v?.function_ids ?? [],
    join_date: toDateInputValue(v?.join_date),
    social_link: v?.social_link ?? '',
    notes: v?.notes ?? '',
    history: v?.history ?? '',
  };
}

const VolunteerFormModal = ({ volunteer, onClose, onSave, isPending }: Props) => {
  const { data: functions, save: saveFunction } = useFunctions();
  const [newFunctionName, setNewFunctionName] = useState('');
  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors },
  } = useForm<VolunteerInput>({ defaultValues: defaults(volunteer) });

  const selectedFunctionIds = useWatch({ control, name: 'function_ids' }) ?? [];
  const selectedFunctions = (functions ?? []).filter((item) => selectedFunctionIds.includes(item.id));
  const availableFunctions = (functions ?? []).filter((item) => item.is_active && !item.is_system && !selectedFunctionIds.includes(item.id));

  const addFunction = (id: number) => {
    setValue('function_ids', [...selectedFunctionIds, id], { shouldDirty: true });
  };

  const removeFunction = (id: number) => {
    setValue('function_ids', selectedFunctionIds.filter((functionId) => functionId !== id), { shouldDirty: true });
  };

  const createFunction = () => {
    const name = newFunctionName.trim();
    if (!name) return;
    saveFunction.mutate(
      { id: null, data: { name } },
      { onSuccess: () => setNewFunctionName('') },
    );
  };

  const submit = handleSubmit((data) => onSave({ id: volunteer?.id ?? null, data }));

  return (
    <FormModal
      title={volunteer ? 'Edycja Danych' : 'Nowy Wolontariusz'}
      onClose={onClose}
      onSubmit={submit}
      isPending={isPending}
    >
      <TextInput label="Imię i Nazwisko" error={errors.full_name?.message} {...register('full_name', rules.required('Imię i nazwisko jest wymagane'))} />
      <TextInput label="Email" autoComplete="off" error={errors.email?.message} {...register('email', rules.requiredEmail())} />
      <div className="grid grid-cols-2 gap-4">
        <TextInput
          label="Telefon"
          autoComplete="off"
          error={errors.phone?.message}
          onInput={(e) => {
            e.currentTarget.value = sanitizePhoneInput(e.currentTarget.value);
          }}
          {...register('phone', rules.requiredPhone())}
        />
        <SelectInput label="Status" {...register('status')}>
          <option value="Aktywny">Aktywny</option>
          <option value="Były">Były</option>
        </SelectInput>
      </div>
      <Field label="Funkcje">
        <div className="space-y-2">
          <SelectInput
            value=""
            onChange={(e) => {
              const id = Number(e.target.value);
              if (id) addFunction(id);
            }}
          >
            <option value="">— wybierz funkcję —</option>
            {availableFunctions.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </SelectInput>

          {selectedFunctions.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {selectedFunctions.map((item) => (
                <span key={item.id} className="inline-flex items-center gap-1 rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-700">
                  {item.name}
                  <button
                    type="button"
                    onClick={() => removeFunction(item.id)}
                    className="text-gray-400 hover:text-rose-500"
                    title="Usuń funkcję"
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <input
              value={newFunctionName}
              onChange={(e) => setNewFunctionName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  createFunction();
                }
              }}
              placeholder="Nowa funkcja..."
              className="w-full border p-2 rounded-md outline-none focus:border-blue-500 text-sm"
            />
            <button
              type="button"
              onClick={createFunction}
              disabled={saveFunction.isPending || !newFunctionName.trim()}
              className="shrink-0 bg-indigo-600 text-white px-3 py-2 rounded-md text-xs font-bold hover:bg-indigo-700 disabled:opacity-50"
            >
              + Dodaj
            </button>
          </div>
        </div>
      </Field>
      <TextInput label="Data przystąpienia" type="date" max="9999-12-31" error={errors.join_date?.message} {...register('join_date', rules.requiredJoinDate())} />
      <TextInput label="Profil społecznościowy (URL)" autoComplete="off" {...register('social_link')} />
      <TextArea label="Notatki" {...register('notes')} />
      <TextArea label="Historia" {...register('history')} />
    </FormModal>
  );
};

export default VolunteerFormModal;
