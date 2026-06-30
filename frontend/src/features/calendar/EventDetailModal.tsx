import Modal from '@/components/ui/Modal';
import { calendarService } from '@/services/calendarService';
import type { CalendarEvent } from '@/types';

interface Props {
  event: CalendarEvent;
  canManage: boolean;
  onClose: () => void;
  onEdit: () => void;
  onCancel: () => void;
  onDelete: () => void;
}

const dateLabel = (event: CalendarEvent) => {
  const options: Intl.DateTimeFormatOptions = event.is_all_day
    ? { dateStyle: 'full' }
    : { dateStyle: 'full', timeStyle: 'short' };
  return `${new Intl.DateTimeFormat('pl-PL', options).format(new Date(event.starts_at))} – ${new Intl.DateTimeFormat('pl-PL', options).format(new Date(event.ends_at))}`;
};

const EventDetailModal = ({ event, canManage, onClose, onEdit, onCancel, onDelete }: Props) => (
  <Modal onClose={onClose} maxWidth="max-w-xl">
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-indigo-600">Wydarzenie</p>
        <h2 className={`mt-1 text-2xl font-bold ${event.status === 'cancelled' ? 'text-gray-400 line-through' : 'text-gray-900'}`}>{event.title}</h2>
      </div>
      <button onClick={onClose} className="text-2xl text-gray-400" aria-label="Zamknij">×</button>
    </div>
    <dl className="mt-6 grid gap-4 text-sm">
      <div><dt className="font-bold text-gray-500">Termin</dt><dd className="mt-1 text-gray-800">{dateLabel(event)}</dd></div>
      <div><dt className="font-bold text-gray-500">Lokalizacja</dt><dd className="mt-1 text-gray-800">{event.location || '—'}</dd></div>
      <div><dt className="font-bold text-gray-500">Opis</dt><dd className="mt-1 whitespace-pre-wrap text-gray-800">{event.description || '—'}</dd></div>
      <div className="grid grid-cols-2 gap-3">
        <div><dt className="font-bold text-gray-500">Status</dt><dd>{event.status === 'published' ? 'Opublikowane' : event.status === 'draft' ? 'Szkic' : 'Anulowane'}</dd></div>
        <div><dt className="font-bold text-gray-500">Widoczność</dt><dd>{event.visibility === 'organization' ? 'Organizacja' : 'Zarządzający'}</dd></div>
      </div>
      <div><dt className="font-bold text-gray-500">Autor</dt><dd>{event.author_name}</dd></div>
      {event.recurrence_rule && <div><dt className="font-bold text-gray-500">Cykliczność</dt><dd>{event.recurrence_rule}</dd></div>}
    </dl>
    <div className="mt-6 flex flex-wrap justify-end gap-2 border-t pt-4">
      <button type="button" onClick={() => calendarService.downloadEvent(event)} className="rounded-lg border px-3 py-2 text-sm font-bold text-gray-600">Pobierz .ics</button>
      {canManage && <button type="button" onClick={onEdit} className="rounded-lg bg-indigo-50 px-3 py-2 text-sm font-bold text-indigo-700">Edytuj</button>}
      {canManage && event.status !== 'cancelled' && <button type="button" onClick={onCancel} className="rounded-lg bg-amber-50 px-3 py-2 text-sm font-bold text-amber-700">Anuluj wydarzenie</button>}
      {canManage && <button type="button" onClick={onDelete} className="rounded-lg bg-rose-50 px-3 py-2 text-sm font-bold text-rose-700">Usuń</button>}
    </div>
  </Modal>
);

export default EventDetailModal;
