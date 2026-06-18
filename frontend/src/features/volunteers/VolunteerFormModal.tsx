import { useForm } from 'react-hook-form';
import FormModal from '@/components/ui/FormModal';
import { TextInput, SelectInput, TextArea } from '@/components/ui/form';
import { rules, sanitizePhoneInput } from '@/lib/validation';
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
    join_date: v?.join_date ?? '',
    social_link: v?.social_link ?? '',
    notes: v?.notes ?? '',
    history: v?.history ?? '',
  };
}

const VolunteerFormModal = ({ volunteer, onClose, onSave, isPending }: Props) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VolunteerInput>({ defaultValues: defaults(volunteer) });

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
      <TextInput label="Data przystąpienia" type="date" max="9999-12-31" error={errors.join_date?.message} {...register('join_date', rules.requiredJoinDate())} />
      <TextInput label="Profil społecznościowy (URL)" autoComplete="off" {...register('social_link')} />
      <TextArea label="Notatki" {...register('notes')} />
      <TextArea label="Historia" {...register('history')} />
    </FormModal>
  );
};

export default VolunteerFormModal;
