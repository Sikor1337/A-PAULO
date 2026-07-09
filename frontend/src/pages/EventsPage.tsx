import { useMemo, useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import CalendarSubscriptionModal from '@/features/calendar/CalendarSubscriptionModal';
import EventDetailModal from '@/features/calendar/EventDetailModal';
import EventFormModal from '@/features/calendar/EventFormModal';
import { expandOccurrences, occurrenceDays } from '@/features/calendar/recurrence';
import { useCalendarEvents } from '@/hooks/useCalendar';
import { useHasPermission } from '@/hooks/usePermissions';
import { useDialogs } from '@/components/ui/dialog/DialogProvider';
import type { CalendarEvent, CalendarEventStatus, CalendarEventVisibility } from '@/types';

const weekdays = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nie'];

const dateKey = (date: Date) => {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
};

const calendarDays = (month: Date) => {
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const mondayOffset = (first.getDay() + 6) % 7;
  const start = new Date(first);
  start.setDate(first.getDate() - mondayOffset);
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
};

const statusClass: Record<CalendarEventStatus, string> = {
  published: 'border-indigo-500 bg-indigo-50 text-indigo-800',
  draft: 'border-amber-500 bg-amber-50 text-amber-800',
  cancelled: 'border-gray-400 bg-gray-100 text-gray-500 line-through',
};

const eventRangeLabel = (event: CalendarEvent) => {
  const options: Intl.DateTimeFormatOptions = event.is_all_day
    ? { dateStyle: 'medium' }
    : { dateStyle: 'medium', timeStyle: 'short' };
  const formatter = new Intl.DateTimeFormat('pl-PL', options);
  return `${formatter.format(new Date(event.starts_at))} – ${formatter.format(new Date(event.ends_at))}`;
};

const EventsPage = () => {
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [view, setView] = useState<'month' | 'list'>('month');
  const [status, setStatus] = useState<CalendarEventStatus | ''>('');
  const [visibility, setVisibility] = useState<CalendarEventVisibility | ''>('');
  const [sort, setSort] = useState<'asc' | 'desc'>('asc');
  const [selected, setSelected] = useState<CalendarEvent | null>(null);
  const [editing, setEditing] = useState<CalendarEvent | null | undefined>(undefined);
  const [initialDate, setInitialDate] = useState<Date | undefined>();
  const [subscriptionOpen, setSubscriptionOpen] = useState(false);
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_EVENTS');
  const { confirm } = useDialogs();

  const days = useMemo(() => calendarDays(month), [month]);
  const [rangeStart, rangeEnd] = useMemo(() => {
    const start = days[0];
    const end = new Date(days[days.length - 1]);
    end.setHours(23, 59, 59, 999);
    return [start, end];
  }, [days]);
  const eventsQuery = useCalendarEvents({
    startsFrom: rangeStart.toISOString(),
    startsTo: rangeEnd.toISOString(),
    status,
    visibility,
    sort,
  });
  const events = useMemo(() => eventsQuery.data ?? [], [eventsQuery.data]);
  const occurrences = useMemo(
    () => expandOccurrences(events, rangeStart, rangeEnd),
    [events, rangeEnd, rangeStart],
  );
  const eventsByDay = useMemo(() => {
    const result = new Map<string, typeof occurrences>();
    occurrences.forEach((event) => {
      occurrenceDays(event).forEach((key) => {
        result.set(key, [...(result.get(key) ?? []), event]);
      });
    });
    return result;
  }, [occurrences]);

  const openNew = (date = new Date()) => {
    setInitialDate(date);
    setEditing(null);
  };
  const moveMonth = (difference: number) => setMonth((current) => new Date(current.getFullYear(), current.getMonth() + difference, 1));
  const monthLabel = new Intl.DateTimeFormat('pl-PL', { month: 'long', year: 'numeric' }).format(month);

  return (
    <PageShell cardClassName="min-h-[calc(100dvh-88px)] overflow-hidden rounded-xl bg-white text-gray-900 shadow-lg lg:min-h-[calc(100dvh-48px)]">
      <header className="border-b px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📅</span>
            <div><h1 className="text-xl font-bold uppercase text-gray-900">Wydarzenia</h1><p className="text-sm text-gray-500">Kalendarz całej organizacji</p></div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => setSubscriptionOpen(true)} className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-bold text-gray-900 shadow-sm hover:bg-gray-50">Subskrybuj .ics</button>
            {canManage && <button type="button" onClick={() => openNew()} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white">+ Nowe wydarzenie</button>}
          </div>
        </div>
        <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => moveMonth(-1)} className="size-9 rounded-lg border text-lg text-gray-600" aria-label="Poprzedni miesiąc">‹</button>
            <button type="button" onClick={() => setMonth(new Date(new Date().getFullYear(), new Date().getMonth(), 1))} className="rounded-lg border px-3 py-2 text-sm font-bold text-gray-600">Dzisiaj</button>
            <button type="button" onClick={() => moveMonth(1)} className="size-9 rounded-lg border text-lg text-gray-600" aria-label="Następny miesiąc">›</button>
            <h2 className="ml-2 min-w-48 text-lg font-bold capitalize text-gray-900">{monthLabel}</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <select value={status} onChange={(event) => setStatus(event.target.value as CalendarEventStatus | '')} className="h-9 rounded-lg border bg-white px-3 text-sm text-gray-600">
              <option value="">Wszystkie statusy</option><option value="published">Opublikowane</option><option value="draft">Szkice</option><option value="cancelled">Anulowane</option>
            </select>
            <select value={visibility} onChange={(event) => setVisibility(event.target.value as CalendarEventVisibility | '')} className="h-9 rounded-lg border bg-white px-3 text-sm text-gray-600">
              <option value="">Każda widoczność</option><option value="organization">Organizacja</option>{canManage && <option value="admins">Zarządzający</option>}
            </select>
            <select value={sort} onChange={(event) => setSort(event.target.value as 'asc' | 'desc')} className="h-9 rounded-lg border bg-white px-3 text-sm text-gray-600" aria-label="Sortowanie wydarzeń">
              <option value="asc">Najpierw najwcześniejsze</option>
              <option value="desc">Najpierw najpóźniejsze</option>
            </select>
            <div className="flex rounded-lg bg-gray-100 p-1">
              <button type="button" onClick={() => setView('month')} className={`rounded-md px-3 py-1 text-xs font-bold ${view === 'month' ? 'bg-white text-indigo-700 shadow' : 'text-gray-500'}`}>Miesiąc</button>
              <button type="button" onClick={() => setView('list')} className={`rounded-md px-3 py-1 text-xs font-bold ${view === 'list' ? 'bg-white text-indigo-700 shadow' : 'text-gray-500'}`}>Lista</button>
            </div>
          </div>
        </div>
      </header>

      {eventsQuery.isError ? (
        <div className="p-12 text-center text-rose-700">Nie udało się pobrać wydarzeń. Spróbuj ponownie.</div>
      ) : eventsQuery.isLoading ? (
        <div className="p-16 text-center text-gray-400">Ładowanie kalendarza…</div>
      ) : view === 'month' ? (
        <div className="overflow-x-auto">
          <div className="min-w-[760px]">
            <div className="grid grid-cols-7 border-b bg-gray-50">
              {weekdays.map((day) => <div key={day} className="px-2 py-2 text-center text-xs font-bold uppercase text-gray-500">{day}</div>)}
            </div>
            <div className="grid grid-cols-7">
              {days.map((day) => {
                const key = dateKey(day);
                const isCurrentMonth = day.getMonth() === month.getMonth();
                const isToday = key === dateKey(new Date());
                return (
                  <div key={key} onDoubleClick={() => canManage && openNew(day)} className={`min-h-28 border-b border-r p-1.5 ${isCurrentMonth ? 'bg-white' : 'bg-gray-50'}`}>
                    <div className={`mb-1 flex size-7 items-center justify-center rounded-full text-xs font-bold ${isToday ? 'bg-indigo-600 text-white' : isCurrentMonth ? 'text-gray-700' : 'text-gray-300'}`}>{day.getDate()}</div>
                    <div className="space-y-1">
                      {(eventsByDay.get(key) ?? []).slice(0, 3).map((event) => (
                        <button key={`${event.occurrence_key}-${key}`} type="button" onClick={() => setSelected(event)} className={`block w-full truncate rounded border-l-4 px-2 py-1 text-left text-[11px] font-bold ${statusClass[event.status]}`} title={event.title}>
                          {!event.is_all_day && <span className="mr-1 font-normal">{new Intl.DateTimeFormat('pl-PL', { hour: '2-digit', minute: '2-digit' }).format(new Date(event.starts_at))}</span>}{event.title}
                        </button>
                      ))}
                      {(eventsByDay.get(key)?.length ?? 0) > 3 && <p className="px-2 text-[10px] font-bold text-gray-400">+ {(eventsByDay.get(key)?.length ?? 0) - 3} więcej</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="divide-y">
          {occurrences.length ? occurrences.map((event) => (
            <button key={event.occurrence_key} type="button" onClick={() => setSelected(event)} className="grid w-full gap-2 px-5 py-4 text-left hover:bg-indigo-50 sm:grid-cols-[180px_1fr_180px] sm:items-center">
              <span className="text-sm font-bold text-indigo-700">{eventRangeLabel(event)}</span>
              <span><span className={`block font-bold ${event.status === 'cancelled' ? 'text-gray-400 line-through' : 'text-gray-900'}`}>{event.title}</span><span className="text-xs text-gray-500">{event.location || 'Bez lokalizacji'}</span></span>
              <span className="text-xs font-bold text-gray-500">{event.visibility === 'organization' ? 'Organizacja' : 'Zarządzający'} · {event.status}</span>
            </button>
          )) : <p className="p-12 text-center text-gray-400">Brak wydarzeń w wybranym okresie.</p>}
        </div>
      )}

      {editing !== undefined && (
        <EventFormModal
          event={editing}
          initialDate={initialDate}
          isPending={eventsQuery.save.isPending}
          onClose={() => setEditing(undefined)}
          onSave={(input) => eventsQuery.save.mutate({ event: editing, input }, { onSuccess: () => setEditing(undefined) })}
        />
      )}
      {selected && (
        <EventDetailModal
          event={selected}
          canManage={canManage}
          onClose={() => setSelected(null)}
          onEdit={() => { setEditing(selected); setSelected(null); }}
          onCancel={async () => {
            if (await confirm({ title: 'Anulować wydarzenie?', message: 'Wydarzenie zostanie oznaczone jako anulowane.', confirmLabel: 'Anuluj wydarzenie' })) {
              eventsQuery.cancel.mutate(selected.id, { onSuccess: () => setSelected(null) });
            }
          }}
          onDelete={async () => {
            if (await confirm({ title: 'Trwale usunąć wydarzenie?', message: 'Tej operacji nie można cofnąć.', confirmLabel: 'Usuń' })) {
              eventsQuery.remove.mutate(selected.id, { onSuccess: () => setSelected(null) });
            }
          }}
        />
      )}
      {subscriptionOpen && <CalendarSubscriptionModal onClose={() => setSubscriptionOpen(false)} />}
    </PageShell>
  );
};

export default EventsPage;
