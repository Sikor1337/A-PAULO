import type { CalendarEvent } from '@/types';

export interface CalendarOccurrence extends CalendarEvent {
  occurrence_key: string;
}

const parseRule = (rule: string) => new Map(
  rule.split(';').map((part) => part.split('=', 2) as [string, string]),
);

const parseUntil = (value?: string) => {
  if (!value) return null;
  const match = value.match(/^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})Z)?$/);
  if (!match) return null;
  const [, year, month, day, hour = '23', minute = '59', second = '59'] = match;
  return new Date(Date.UTC(+year, +month - 1, +day, +hour, +minute, +second));
};

const addMonths = (date: Date, months: number) => {
  const next = new Date(date);
  const day = next.getDate();
  next.setDate(1);
  next.setMonth(next.getMonth() + months);
  const lastDay = new Date(next.getFullYear(), next.getMonth() + 1, 0).getDate();
  next.setDate(Math.min(day, lastDay));
  return next;
};

const nextStart = (current: Date, frequency: string, interval: number) => {
  const next = new Date(current);
  if (frequency === 'DAILY') next.setDate(next.getDate() + interval);
  else if (frequency === 'WEEKLY') next.setDate(next.getDate() + 7 * interval);
  else if (frequency === 'MONTHLY') return addMonths(next, interval);
  else if (frequency === 'YEARLY') return addMonths(next, 12 * interval);
  return next;
};

export const expandOccurrences = (
  events: CalendarEvent[],
  rangeStart: Date,
  rangeEnd: Date,
): CalendarOccurrence[] => {
  const occurrences: CalendarOccurrence[] = [];
  events.forEach((event) => {
    const baseStart = new Date(event.starts_at);
    const duration = new Date(event.ends_at).getTime() - baseStart.getTime();
    const rule = event.recurrence_rule ? parseRule(event.recurrence_rule) : null;
    const frequency = rule?.get('FREQ');
    const interval = Math.max(1, Number(rule?.get('INTERVAL') ?? 1));
    const count = Math.max(1, Number(rule?.get('COUNT') ?? Number.MAX_SAFE_INTEGER));
    const until = parseUntil(rule?.get('UNTIL'));
    let start = baseStart;
    let index = 0;

    while (index < count && index < 5000) {
      if (until && start > until) break;
      const end = new Date(start.getTime() + duration);
      if (end >= rangeStart && start <= rangeEnd) {
        occurrences.push({
          ...event,
          starts_at: start.toISOString(),
          ends_at: end.toISOString(),
          occurrence_key: `${event.id}-${start.toISOString()}`,
        });
      }
      if (!frequency || start > rangeEnd) break;
      const following = nextStart(start, frequency, interval);
      if (following.getTime() === start.getTime()) break;
      start = following;
      index += 1;
    }
  });
  return occurrences.sort((left, right) => (
    new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime()
  ));
};

export const occurrenceDays = (event: CalendarOccurrence): string[] => {
  const start = new Date(event.starts_at);
  const end = new Date(event.ends_at);
  const day = new Date(start.getFullYear(), start.getMonth(), start.getDate());
  const last = new Date(end.getFullYear(), end.getMonth(), end.getDate());
  const result: string[] = [];
  while (day <= last && result.length < 370) {
    const local = new Date(day.getTime() - day.getTimezoneOffset() * 60_000);
    result.push(local.toISOString().slice(0, 10));
    day.setDate(day.getDate() + 1);
  }
  return result;
};
