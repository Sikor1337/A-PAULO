import { useForm } from 'react-hook-form';
import FormModal from '@/components/ui/FormModal';
import { Checkbox, SelectInput, TextInput } from '@/components/ui/form';
import { rules } from '@/lib/validation';
import type { AdminUser, AdminUserInput } from '@/types';

interface Props {
  user: AdminUser | null;
  onClose: () => void;
  onSave: (args: { id: number | null; data: AdminUserInput }) => void;
  isPending: boolean;
}

const defaults = (user: AdminUser | null): AdminUserInput => ({
  username: user?.username ?? '',
  email: user?.email ?? '',
  first_name: user?.first_name ?? '',
  last_name: user?.last_name ?? '',
  status: user?.status ?? 'regular',
  is_active: user?.is_active ?? true,
  password: '',
});

const UserFormModal = ({ user, onClose, onSave, isPending }: Props) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AdminUserInput>({ defaultValues: defaults(user) });

  const submit = handleSubmit((data) => {
    const payload: AdminUserInput = {
      ...data,
      username: data.username.trim(),
      email: data.email.trim(),
      first_name: data.first_name?.trim() ?? '',
      last_name: data.last_name?.trim() ?? '',
      password: data.password?.trim() || undefined,
    };

    onSave({ id: user?.id ?? null, data: payload });
  });

  return (
    <FormModal
      title={user ? 'Edytuj użytkownika' : 'Nowy użytkownik'}
      onClose={onClose}
      onSubmit={submit}
      isPending={isPending}
      submitLabel={user ? 'Zapisz' : 'Dodaj'}
    >
      <div className="grid grid-cols-2 gap-4">
        <TextInput
          label="Imię"
          error={errors.first_name?.message}
          {...register('first_name')}
        />
        <TextInput
          label="Nazwisko"
          error={errors.last_name?.message}
          {...register('last_name')}
        />
      </div>
      <TextInput
        label="Email"
        type="email"
        autoComplete="off"
        error={errors.email?.message}
        {...register('email', rules.requiredEmail())}
      />
      <TextInput
        label="Nazwa użytkownika"
        autoComplete="off"
        error={errors.username?.message}
        {...register('username', rules.required('Nazwa użytkownika jest wymagana'))}
      />
      <div className="grid grid-cols-2 gap-4">
        <SelectInput label="Rola" {...register('status')}>
          <option value="regular">Użytkownik</option>
          <option value="admin">Administrator</option>
        </SelectInput>
        <div className="flex items-end pb-2">
          <Checkbox label="Aktywny" {...register('is_active')} />
        </div>
      </div>
      <TextInput
        label={user ? 'Nowe hasło (opcjonalnie)' : 'Hasło'}
        type="password"
        autoComplete="new-password"
        error={errors.password?.message}
        {...register('password', {
          validate: (value) => Boolean(user) || Boolean(value?.trim()) || 'Hasło jest wymagane',
          minLength: { value: 6, message: 'Minimum 6 znaków' },
        })}
      />
    </FormModal>
  );
};

export default UserFormModal;
