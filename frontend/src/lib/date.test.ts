import { describe, expect, it } from 'vitest';
import { formatDate, toDateInputValue } from './date';

describe('date helpers', () => {
  it('formats backend ISO date strings for display', () => {
    expect(formatDate('2026-06-07T00:00:00')).toBe('07.06.2026');
    expect(formatDate('2026-12-24')).toBe('24.12.2026');
  });

  it('returns an empty string for missing dates', () => {
    expect(formatDate()).toBe('');
    expect(formatDate(null)).toBe('');
    expect(toDateInputValue()).toBe('');
    expect(toDateInputValue(null)).toBe('');
  });

  it('normalizes ISO date strings for date inputs', () => {
    expect(toDateInputValue('2026-06-07T15:30:00')).toBe('2026-06-07');
  });

  it('leaves malformed display values unchanged', () => {
    expect(formatDate('2026')).toBe('2026');
  });
});
