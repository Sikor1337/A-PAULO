import { describe, expect, it } from 'vitest';
import { EMAIL_REGEX, POLISH_PHONE_REGEX, rules, sanitizePhoneInput } from './validation';

describe('validation helpers', () => {
  it('accepts supported Polish phone formats', () => {
    expect(POLISH_PHONE_REGEX.test('+48 123 456 789')).toBe(true);
    expect(POLISH_PHONE_REGEX.test('123-456-789')).toBe(true);
    expect(POLISH_PHONE_REGEX.test('123456789')).toBe(true);
  });

  it('rejects invalid phone formats', () => {
    expect(POLISH_PHONE_REGEX.test('123 456')).toBe(false);
    expect(POLISH_PHONE_REGEX.test('+49 123 456 789')).toBe(false);
  });

  it('validates basic email formats', () => {
    expect(EMAIL_REGEX.test('anna.nowak@example.org')).toBe(true);
    expect(EMAIL_REGEX.test('anna.nowak')).toBe(false);
  });

  it('keeps only phone-safe characters in sanitized phone input', () => {
    expect(sanitizePhoneInput('+48 (123) abc-456!789')).toBe('+48 (123) -456789');
  });

  it('rejects years longer than four digits in join date rules', () => {
    const validation = rules.requiredJoinDate().validate;

    expect(validation?.('2026-06-07')).toBe(true);
    expect(validation?.('12026-06-07')).toBe('Niepoprawny format roku (maksymalnie 4 cyfry)');
  });
});
