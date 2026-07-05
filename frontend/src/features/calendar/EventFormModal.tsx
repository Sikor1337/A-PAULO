import { useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import Modal from '@/components/ui/Modal';
import type { CalendarEvent, CalendarEventInput, CalendarEventStatus, CalendarEventVisibility } from '@/types';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';

interface Props {
  event: CalendarEvent | null;
  initialDate?: Date;
  isPending: boolean;
  onClose: () => void;
  onSave: (input: CalendarEventInput) => void;
}

interface FormValues {
  title: string;
  description: string;
  startsAt: string;
  endsAt: string;
  timezone: string;
  isAllDay: boolean;
  location: string;
  recurrenceRule: string;
  recurrenceUntil: string;
  status: CalendarEventStatus;
  visibility: CalendarEventVisibility;
}

const localDateTime = (value: string | Date, allDay = false) => {
  const date = value instanceof Date ? value : new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString();
  return allDay ? local.slice(0, 10) : local.slice(0, 16);
};

const defaults = (event: CalendarEvent | null, initialDate?: Date): FormValues => {
  const start = event ? new Date(event.starts_at) : initialDate ?? new Date();
  const end = event ? new Date(event.ends_at) : new Date(start.getTime() + 60 * 60_000);
  return {
    title: event?.title ?? '',
    description: event?.description ?? '',
    startsAt: localDateTime(start, event?.is_all_day),
    endsAt: localDateTime(end, event?.is_all_day),
    timezone: event?.timezone ?? 'Europe/Warsaw',
    isAllDay: event?.is_all_day ?? false,
    location: event?.location ?? '',
    recurrenceRule: event?.recurrence_rule ?? '',
    recurrenceUntil: event?.recurrence_rule?.match(/UNTIL=(\d{4})(\d{2})(\d{2})/)?.slice(1, 4).join('-') ?? '',
    status: event?.status ?? 'published',
    visibility: event?.visibility ?? 'organization',
  };
};

const EventFormModal = ({ event, initialDate, isPending, onClose, onSave }: Props) => {
  const { control, register, handleSubmit, setValue, formState: { errors, isDirty } } = useForm<FormValues>({
    defaultValues: defaults(event, initialDate),
  });
  const confirmDiscard = useUnsavedChanges(isDirty && !isPending);
  const close = () => {
    if (confirmDiscard()) onClose();
  };
  const isAllDay = useWatch({ control, name: 'isAllDay' });
  const recurrenceRule = useWatch({ control, name: 'recurrenceRule' });

  useEffect(() => {
    if (!isAllDay || event) return;
    const day = localDateTime(initialDate ?? new Date(), true);
    setValue('startsAt', day);
    setValue('endsAt', day);
  }, [event, initialDate, isAllDay, setValue]);

  const submit = handleSubmit((values) => {
    const start = new Date(isAllDay ? `${values.startsAt}T00:00:00` : values.startsAt);
    const end = new Date(isAllDay ? `${values.endsAt}T00:00:00` : values.endsAt);
    if (end < start) {
      alert('Data zakończenia nie może być wcześniejsza od rozpoczęcia.');
      return;
    }
    const baseRule = values.recurrenceRule
      .split(';')
      .filter((part) => part && !part.startsWith('UNTIL='))
      .join(';');
    const recurrence = baseRule && values.recurrenceUntil
      ? `${baseRule};UNTIL=${values.recurrenceUntil.replaceAll('-', '')}T235959Z`
      : baseRule;
    onSave({
      title: values.title.trim(),
      description: values.description.trim(),
      starts_at: start.toISOString(),
      ends_at: end.toISOString(),
      timezone: values.timezone,
      is_all_day: values.isAllDay,
      location: values.location.trim(),
      recurrence_rule: recurrence || null,
      status: values.status,
      visibility: values.visibility,
    });
  });

  const inputClass = 'mt-1 h-10 w-full rounded-lg border border-gray-200 px-3 text-sm outline-none focus:border-indigo-500';
  return (
    <Modal onClose={close} maxWidth="max-w-2xl">
      <form onSubmit={submit}>
        <h2 className="text-xl font-bold text-gray-900">{event ? 'Edytuj wydarzenie' : 'Nowe wydarzenie'}</h2>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-bold text-gray-700">
            Tytuł
            <input {...register('title', { required: 'Tytuł jest wymagany' })} className={inputClass} autoFocus />
            {errors.title && <span className="text-xs text-rose-600">{errors.title.message}</span>}
          </label>
          <label className="block text-sm font-bold text-gray-700">
            Opis
            <textarea {...register('description')} rows={4} className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-indigo-500" />
          </label>
          <label className="flex items-center gap-2 text-sm font-bold text-gray-700">
            <input type="checkbox" {...register('isAllDay')} /> Cały dzień
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-bold text-gray-700">
              Początek
              <input type={isAllDay ? 'date' : 'datetime-local'} {...register('startsAt', { required: true })} className={inputClass} />
            </label>
            <label className="text-sm font-bold text-gray-700">
              Koniec
              <input type={isAllDay ? 'date' : 'datetime-local'} {...register('endsAt', { required: true })} className={inputClass} />
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-bold text-gray-700">
              Strefa czasowa
              <select {...register('timezone')} className={inputClass}>
                <option value="Europe/Warsaw">Europe/Warsaw</option>
                <option value="UTC">UTC</option>
              </select>
            </label>
            <label className="text-sm font-bold text-gray-700">
              Lokalizacja
              <input {...register('location')} className={inputClass} />
            </label>
          </div>
          <label className="block text-sm font-bold text-gray-700">
            Powtarzanie
            <select {...register('recurrenceRule')} className={inputClass}>
              <option value="">Nie powtarza się</option>
              <option value="FREQ=DAILY">Codziennie</option>
              <option value="FREQ=WEEKLY">Co tydzień</option>
              <option value="FREQ=MONTHLY">Co miesiąc</option>
              <option value="FREQ=YEARLY">Co rok</option>
              {event?.recurrence_rule && !['FREQ=DAILY', 'FREQ=WEEKLY', 'FREQ=MONTHLY', 'FREQ=YEARLY'].includes(event.recurrence_rule) && (
                <option value={event.recurrence_rule}>{event.recurrence_rule}</option>
              )}
            </select>
          </label>
          {recurrenceRule && (
            <label className="block text-sm font-bold text-gray-700">
              Powtarzaj do
              <input type="date" {...register('recurrenceUntil')} className={inputClass} />
            </label>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-bold text-gray-700">
              Status
              <select {...register('status')} className={inputClass}>
                <option value="published">Opublikowane</option>
                <option value="draft">Szkic</option>
                {event?.status === 'cancelled' && <option value="cancelled">Anulowane</option>}
              </select>
            </label>
            <label className="text-sm font-bold text-gray-700">
              Widoczność
              <select {...register('visibility')} className={inputClass}>
                <option value="organization">Cała organizacja</option>
                <option value="admins">Zarządzający wydarzeniami</option>
              </select>
            </label>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" onClick={close} className="rounded-lg border px-4 py-2 text-sm font-bold text-gray-600">Anuluj</button>
          <button disabled={isPending} className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white disabled:opacity-50">
            {isPending ? 'Zapisywanie…' : 'Zapisz'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default EventFormModal;
