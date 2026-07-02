import { describe, expect, it, vi } from 'vitest';
import { buildVolunteerColumns } from './volunteerColumns';

const handlers = {
  onSelect: vi.fn(),
  onEdit: vi.fn(),
  onDelete: vi.fn(),
};

describe('buildVolunteerColumns', () => {
  it('keeps data columns and hides only actions for a read-only user', () => {
    const columns = buildVolunteerColumns({ ...handlers, canManage: false });

    expect(columns.map((column) => column.id)).toEqual([
      'full_name',
      'email',
      'phone',
      'assigned_groups',
      'functions',
      'status',
    ]);
  });

  it('adds actions for a user with volunteer management permission', () => {
    const columns = buildVolunteerColumns({ ...handlers, canManage: true });

    expect(columns.at(-1)?.id).toBe('actions');
  });
});
