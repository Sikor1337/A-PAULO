/**
 * Date helpers for the UI.
 *
 * The backend stores dates as `DateTime`, so the API returns full ISO strings
 * like "2026-06-07T00:00:00". These helpers strip the time component for
 * display and for `<input type="date">`, which only accepts "YYYY-MM-DD".
 */

/** Formats an ISO date/datetime string to Polish `DD.MM.YYYY`. Returns '' when empty. */
export function formatDate(value?: string | null): string {
  if (!value) return '';
  const [y, m, d] = value.slice(0, 10).split('-');
  if (!y || !m || !d) return value;
  return `${d}.${m}.${y}`;
}

/** Normalizes an ISO date/datetime to a `YYYY-MM-DD` value for `<input type="date">`. */
export function toDateInputValue(value?: string | null): string {
  return value ? value.slice(0, 10) : '';
}
