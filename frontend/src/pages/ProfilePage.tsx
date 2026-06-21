import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import PageShell from '@/components/layout/PageShell';
import { TextInput } from '@/components/ui/form';
import { parseApiError } from '@/lib/errors';
import { rules } from '@/lib/validation';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/stores/authStore';

interface ProfileFormData {
  email: string;
  first_name: string;
  last_name: string;
  current_password: string;
  new_password: string;
  confirm_password: string;
}

const EMPTY_PASSWORDS = { current_password: '', new_password: '', confirm_password: '' };

const displayValue = (value?: string | null) => value || '-';

const ProfilePage = () => {
  const { updateUser } = useAuthStore();
  const { data: profile, isLoading: isProfileLoading, refetch } = useQuery({
    queryKey: ['me'],
    queryFn: authService.getUserProfile,
  });
  const [isEditing, setIsEditing] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<ProfileFormData>({
    defaultValues: { email: '', first_name: '', last_name: '', ...EMPTY_PASSWORDS },
  });

  useEffect(() => {
    if (profile && !isEditing) {
      reset({
        email: profile.email,
        first_name: profile.first_name,
        last_name: profile.last_name,
        ...EMPTY_PASSWORDS,
      });
    }
  }, [isEditing, profile, reset]);

  const newPassword = watch('new_password');

  const cancelEdit = () => {
    if (profile) {
      reset({
        email: profile.email,
        first_name: profile.first_name,
        last_name: profile.last_name,
        ...EMPTY_PASSWORDS,
      });
    }
    setErrorMsg('');
    setIsEditing(false);
  };

  const onSubmit = handleSubmit(async (data) => {
    setSuccessMsg('');
    setErrorMsg('');
    setIsSaving(true);
    try {
      const payload: Record<string, string> = {
        email: data.email,
        first_name: data.first_name,
        last_name: data.last_name,
      };
      if (data.new_password) {
        payload.current_password = data.current_password;
        payload.new_password = data.new_password;
      }

      const updated = await authService.updateProfile(payload);
      updateUser({
        id: updated.id,
        email: updated.email,
        first_name: updated.first_name,
        last_name: updated.last_name,
        role: updated.status === 'admin' ? 'admin' : 'volunteer',
      });
      setSuccessMsg('Zapisano zmiany.');
      setIsEditing(false);
      reset({ email: updated.email, first_name: updated.first_name, last_name: updated.last_name, ...EMPTY_PASSWORDS });
      refetch();
    } catch (err) {
      setErrorMsg(parseApiError(err, 'Nie udało się zapisać zmian.'));
    } finally {
      setIsSaving(false);
    }
  });

  return (
    <PageShell cardClassName="bg-white rounded-xl shadow-lg max-w-2xl mx-auto p-8">
      <div className="flex items-center justify-between gap-4 mb-6 border-b pb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">👤</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Moje konto</h1>
        </div>
        {!isEditing && (
          <button
            type="button"
            onClick={() => {
              setSuccessMsg('');
              setErrorMsg('');
              setIsEditing(true);
            }}
            disabled={isProfileLoading || !profile}
            className="bg-indigo-600 text-white px-5 py-2 rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            Edytuj
          </button>
        )}
      </div>

      {successMsg && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-md text-sm font-medium">{successMsg}</div>
      )}
      {errorMsg && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm font-medium">{errorMsg}</div>}

      {!isEditing ? (
        <div className="grid grid-cols-2 gap-5 text-sm">
          <div>
            <p className="text-[10px] font-black uppercase text-gray-400 mb-1">Imię</p>
            <p className="text-gray-800 font-medium">{displayValue(profile?.first_name)}</p>
          </div>
          <div>
            <p className="text-[10px] font-black uppercase text-gray-400 mb-1">Nazwisko</p>
            <p className="text-gray-800 font-medium">{displayValue(profile?.last_name)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-[10px] font-black uppercase text-gray-400 mb-1">Email</p>
            <p className="text-gray-800 font-medium">{displayValue(profile?.email)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-[10px] font-black uppercase text-gray-400 mb-1">Nazwa użytkownika</p>
            <p className="text-gray-800 font-medium">{displayValue(profile?.username)}</p>
          </div>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="grid grid-cols-2 gap-4">
            <TextInput label="Imię" {...register('first_name')} />
            <TextInput label="Nazwisko" {...register('last_name')} />
          </div>
          <TextInput label="Email" type="email" error={errors.email?.message} {...register('email', rules.requiredEmail())} />
          {profile && (
            <div>
              <p className="text-[10px] font-black uppercase text-gray-400 mb-1">Nazwa użytkownika</p>
              <p className="text-sm text-gray-600">{profile.username}</p>
            </div>
          )}

          <div className="pt-4 border-t">
            <h2 className="text-sm font-bold text-gray-700 mb-3">Zmiana hasła</h2>
            <TextInput label="Obecne hasło" type="password" autoComplete="current-password" {...register('current_password')} />
            <div className="grid grid-cols-2 gap-4 mt-4">
              <TextInput
                label="Nowe hasło"
                type="password"
                autoComplete="new-password"
                error={errors.new_password?.message}
                {...register('new_password', { minLength: { value: 8, message: 'Minimum 8 znaków' } })}
              />
              <TextInput
                label="Powtórz nowe hasło"
                type="password"
                autoComplete="new-password"
                error={errors.confirm_password?.message}
                {...register('confirm_password', {
                  validate: (value) => !newPassword || value === newPassword || 'Hasła nie są zgodne',
                })}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={cancelEdit} className="px-5 py-2 text-gray-400 font-bold hover:text-gray-600">
              Anuluj
            </button>
            <button
              type="submit"
              disabled={isSaving || isProfileLoading}
              className="bg-indigo-600 text-white px-8 py-2.5 rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSaving ? 'Zapisywanie...' : 'Zapisz zmiany'}
            </button>
          </div>
        </form>
      )}
    </PageShell>
  );
};

export default ProfilePage;
