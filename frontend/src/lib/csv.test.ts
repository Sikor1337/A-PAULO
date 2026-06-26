import { describe, expect, it, vi } from 'vitest';
import { exportRowsToCsv } from './csv';

describe('exportRowsToCsv', () => {
  it('creates a downloadable CSV with escaped values', async () => {
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:csv');
    const revokeObjectURL = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);

    exportRowsToCsv(
      'volunteers.csv',
      [
        { header: 'Name', value: (row) => row.name },
        { header: 'Notes', value: (row) => row.notes },
      ],
      [{ name: 'Anna, Nowak', notes: 'Says "hello"\nOften' }],
    );

    const blob = createObjectURL.mock.calls[0]?.[0] as Blob;
    const bytes = new Uint8Array(await blob.arrayBuffer());

    expect([...bytes.slice(0, 3)]).toEqual([0xef, 0xbb, 0xbf]);
    await expect(blob.text()).resolves.toBe('Name,Notes\n"Anna, Nowak","Says ""hello""\nOften"');
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:csv');
  });
});
