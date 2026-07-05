import { AxiosError } from 'axios';
import { describe, expect, it } from 'vitest';
import { parseApiError } from './errors';

describe('parseApiError', () => {
  it('turns FastAPI validation details into readable text', () => {
    const error = new AxiosError('validation', 'ERR_BAD_REQUEST', undefined, undefined, {
      data: { detail: [{ msg: 'Hasło jest zbyt krótkie' }] },
      status: 422,
      statusText: 'Unprocessable Content',
      headers: {},
      config: { headers: {} } as never,
    });

    expect(parseApiError(error)).toBe('Hasło jest zbyt krótkie');
  });
});
