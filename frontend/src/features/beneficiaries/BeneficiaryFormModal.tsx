import { useForm } from 'react-hook-form';
import FormModal from '@/components/ui/FormModal';
import { TextInput, SelectInput, TextArea, Checkbox } from '@/components/ui/form';
import { rules, sanitizePhoneInput } from '@/lib/validation';
import type { Beneficiary, BeneficiaryInput } from '@/types';

interface Props {
  beneficiary: Beneficiary | null;
  onClose: () => void;
  onSave: (args: { id: number | null; data: BeneficiaryInput }) => void;
  isPending: boolean;
}

function defaults(b: Beneficiary | null): BeneficiaryInput {
  return {
    full_name: b?.full_name ?? '',
    address: b?.address ?? '',
    phone: b?.phone ?? '',
    family_phone: b?.family_phone ?? '',
    status: b?.status ?? 'OBECNY',
    bo_enrolled: b?.bo_enrolled ?? false,
    description: b?.description ?? '',
    last_priest_visit: b?.last_priest_visit ?? '',
    last_volunteer_meeting: b?.last_volunteer_meeting ?? '',
    history: b?.history ?? '',
  };
}

const phoneSanitizer = (e: React.FormEvent<HTMLInputElement>) => {
  e.currentTarget.value = sanitizePhoneInput(e.currentTarget.value);
};

const BeneficiaryFormModal = ({ beneficiary, onClose, onSave, isPending }: Props) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BeneficiaryInput>({ defaultValues: defaults(beneficiary) });

  const submit = handleSubmit((form) => {
    // NOTE: preserves prior behaviour — the form has no group field and always sends group: null.
    const data: BeneficiaryInput = {
      ...form,
      group: null,
      last_priest_visit: form.last_priest_visit || null,
      last_volunteer_meeting: form.last_volunteer_meeting || null,
    };
    onSave({ id: beneficiary?.id ?? null, data });
  });

  return (
    <FormModal
      title={beneficiary ? 'Edycja Danych' : 'Nowy Podopieczny'}
      onClose={onClose}
      onSubmit={submit}
      isPending={isPending}
    >
      <TextInput label="Imię i Nazwisko" error={errors.full_name?.message} {...register('full_name', rules.required('Imię i nazwisko jest wymagane'))} />
      <TextInput label="Adres" autoComplete="off" error={errors.address?.message} {...register('address', rules.required('Adres jest wymagany'))} />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <TextInput label="Telefon" error={errors.phone?.message} onInput={phoneSanitizer} {...register('phone', rules.requiredPhone())} />
        <TextInput
          label="Telefon rodziny"
          autoComplete="off"
          error={errors.family_phone?.message}
          onInput={phoneSanitizer}
          {...register('family_phone', rules.requiredPhone('Telefon rodziny jest wymagany'))}
        />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <SelectInput label="Status" {...register('status')}>
          <option value="OBECNY">Obecny</option>
          <option value="ZMARŁY">Zmarły</option>
          <option value="BYŁY">Były</option>
          <option value="DPS_ZOL">DPS/ZOL</option>
        </SelectInput>
        <div className="flex items-end pb-1">
          <Checkbox label="Objęty BO" {...register('bo_enrolled')} />
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-[10px] font-black uppercase text-gray-400">Grupa</dt>
          <dd className="text-gray-700">{beneficiary?.group_name || '—'}</dd>
        </div>
        <TextArea label="Opis / Notatki" {...register('description')} />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <TextInput label="Ostatnia wizyta księdza" type="date" max="9999-12-31" {...register('last_priest_visit')} />
        <TextInput label="Ostatnie spotkanie z wol." type="date" max="9999-12-31" {...register('last_volunteer_meeting')} />
      </div>
      <TextArea label="Historia" {...register('history')} />
    </FormModal>
  );
};

export default BeneficiaryFormModal;
