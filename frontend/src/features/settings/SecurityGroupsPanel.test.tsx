import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useSecurityGroups } from '@/hooks/usePermissions';
import SecurityGroupsPanel from './SecurityGroupsPanel';

vi.mock('@/hooks/useUnsavedChanges', () => ({
  useUnsavedChanges: () => () => true,
}));

vi.mock('@/hooks/usePermissions', () => ({
  useSecurityGroups: vi.fn(),
}));

const mockedUseSecurityGroups = vi.mocked(useSecurityGroups);
const saveMutate = vi.fn();

describe('SecurityGroupsPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockedUseSecurityGroups.mockReturnValue({
      permissions: { data: [] },
      groups: {
        data: [{
          id: 7,
          name: 'Reviewer',
          description: '',
          is_system: false,
          system_key: null,
          permissions: [],
          user_ids: [],
          created_at: '2026-07-02T00:00:00Z',
          updated_at: '2026-07-02T00:00:00Z',
        }],
      },
      create: { mutate: vi.fn() },
      save: { mutate: saveMutate, isPending: false },
      remove: { mutate: vi.fn() },
    } as never);
  });

  it('keeps save clickable after editing description and sends one complete request', () => {
    render(<SecurityGroupsPanel users={[]} canManage />);

    fireEvent.change(screen.getByLabelText('Opis'), {
      target: { value: 'Opis grupy' },
    });
    const saveButton = screen.getByRole('button', { name: 'Zapisz zmiany' });
    expect(saveButton).toBeEnabled();
    fireEvent.click(saveButton);

    expect(saveMutate).toHaveBeenCalledTimes(1);
    expect(saveMutate.mock.calls[0]?.[0]).toEqual({
      id: 7,
      input: {
        name: 'Reviewer',
        description: 'Opis grupy',
        permission_codes: [],
        user_ids: [],
      },
    });
  });
});
