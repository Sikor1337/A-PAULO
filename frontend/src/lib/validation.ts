/** Polish phone: optional +48 and 3-3-3 digit groups separated by space/dash. Mirrors the backend regex. */
export const POLISH_PHONE_REGEX = /^(?:\+48)?[ -]?\d{3}[ -]?\d{3}[ -]?\d{3}$/;

/** Loose email check, matching the previous inline regex in VolunteersPage. */
export const EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;

/**
 * Narrow subset of react-hook-form's RegisterOptions — just the rule keys we use.
 * Kept field-agnostic so it stays assignable to `register(name, rule)` for any field.
 */
export interface FieldRule {
  required?: string;
  pattern?: { value: RegExp; message: string };
  validate?: (value: unknown) => string | true;
}

/** Reusable `register` rule sets, with the original Polish messages. */
export const rules = {
  required: (message: string): FieldRule => ({ required: message }),

  requiredPhone: (message = 'Numer telefonu jest wymagany'): FieldRule => ({
    required: message,
    pattern: { value: POLISH_PHONE_REGEX, message: 'Podaj prawidłowy polski numer (np. +48 123 456 789)' },
  }),

  requiredEmail: (message = 'Email jest wymagany'): FieldRule => ({
    required: message,
    pattern: { value: EMAIL_REGEX, message: 'Niepoprawny format email' },
  }),

  requiredJoinDate: (message = 'Data przystąpienia jest wymagana'): FieldRule => ({
    required: message,
    validate: (value: unknown) => {
      const year = String(value ?? '').split('-')[0];
      if (year && year.length > 4) return 'Niepoprawny format roku (maksymalnie 4 cyfry)';
      return true;
    },
  }),
} as const;

/** Strips characters that are not valid in a phone field (used as an onInput sanitizer). */
export const sanitizePhoneInput = (value: string): string => value.replace(/[^0-9+\s\-()]/g, '');
