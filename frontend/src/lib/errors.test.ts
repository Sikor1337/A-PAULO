import { AxiosError } from 'axios';
import { describe, expect, it } from 'vitest';
import { parseApiError } from './errors';

describe('parseApiError', () => {
  it('shows validation messages instead of raw JSON', () => {
    const error = new AxiosError('validation');
    error.response = {
      data: {
        detail: [{
          type: 'too_short',
          loc: ['body', 'fields'],
          msg: 'Lista pytań jest zbyt krótka.',
        }],
      },
      status: 422,
      statusText: 'Unprocessable Content',
      headers: {},
      config: {} as never,
    };

    expect(parseApiError(error)).toBe('Lista pytań jest zbyt krótka.');
  });
});
