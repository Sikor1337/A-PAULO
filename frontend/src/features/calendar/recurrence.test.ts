import { describe, expect, it } from 'vitest';
import type { CalendarEvent } from '@/types';
import { expandOccurrences, occurrenceDays } from './recurrence';

const event = (overrides: Partial<CalendarEvent> = {}): CalendarEvent => ({
  id: 1,
  uid: 'event@a-paulo',
  title: 'Spotkanie',
  description: '',
  starts_at: '2026-07-01T10:00:00.000Z',
  ends_at: '2026-07-01T11:00:00.000Z',
  timezone: 'Europe/Warsaw',
  is_all_day: false,
  location: '',
  recurrence_rule: null,
  status: 'published',
  visibility: 'organization',
  author_id: 1,
  author_name: 'Admin',
  sequence: 0,
  created_at: '2026-07-01T00:00:00.000Z',
  updated_at: '2026-07-01T00:00:00.000Z',
  ...overrides,
});

describe('calendar recurrence', () => {
  it('expands daily events until the selected end date', () => {
    const result = expandOccurrences(
      [event({ recurrence_rule: 'FREQ=DAILY;UNTIL=20260704T235959Z' })],
      new Date('2026-07-01T00:00:00Z'),
      new Date('2026-07-31T23:59:59Z'),
    );

    expect(result).toHaveLength(4);
    expect(result.map((item) => item.starts_at.slice(0, 10))).toEqual([
      '2026-07-01', '2026-07-02', '2026-07-03', '2026-07-04',
    ]);
  });

  it('returns every day covered by a multi-day event', () => {
    const [occurrence] = expandOccurrences(
      [event({ ends_at: '2026-07-03T11:00:00.000Z' })],
      new Date('2026-07-01T00:00:00Z'),
      new Date('2026-07-31T23:59:59Z'),
    );

    expect(occurrenceDays(occurrence)).toEqual(['2026-07-01', '2026-07-02', '2026-07-03']);
  });
});
