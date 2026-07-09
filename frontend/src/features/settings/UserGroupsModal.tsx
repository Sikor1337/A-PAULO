import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Modal from '@/components/ui/Modal';
import { useDialogs } from '@/components/ui/dialog/DialogProvider';
import { parseApiError } from '@/lib/errors';
import { permissionService } from '@/services/permissionService';
import type { AdminUser, SecurityGroup } from '@/types';

interface Props {
  user: AdminUser;
  groups: SecurityGroup[];
  onClose: () => void;
}

const UserGroupsModal = ({ user, groups, onClose }: Props) => {
  const queryClient = useQueryClient();
  const { alert } = useDialogs();
  const membership = useQuery({
    queryKey: ['security-user-groups', user.id],
    queryFn: () => permissionService.getUserGroups(user.id),
  });
  const [changedSelection, setChangedSelection] = useState<number[] | null>(null);
  const selected = changedSelection ?? membership.data ?? [];

  const save = useMutation({
    mutationFn: () => permissionService.setUserGroups(user.id, selected),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-groups'] });
      queryClient.invalidateQueries({ queryKey: ['security-user-groups', user.id] });
      if (user.id) queryClient.invalidateQueries({ queryKey: ['my-permissions'] });
      onClose();
    },
    onError: (error) => { void alert({ title: 'Błąd', message: parseApiError(error, 'Nie udało się przypisać grup.') }); },
  });

  return (
    <Modal onClose={onClose}>
      <h2 className="mb-4 text-xl font-bold text-gray-900">Grupy użytkownika: {user.email}</h2>
      <div className="space-y-2">
        {groups.map((group) => (
          <label key={group.id} className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 hover:bg-gray-50">
            <input
              type="checkbox"
              checked={selected.includes(group.id)}
              onChange={() => setChangedSelection(selected.includes(group.id)
                ? selected.filter((id) => id !== group.id)
                : [...selected, group.id])}
              className="mt-1 size-4"
            />
            <span>
              <span className="block text-sm font-bold text-gray-800">
                {group.name} {group.is_system && <span className="text-xs text-indigo-600">systemowa</span>}
              </span>
              <span className="text-xs text-gray-500">{group.description || 'Brak opisu'}</span>
            </span>
          </label>
        ))}
      </div>
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" onClick={onClose} className="rounded-lg border px-4 py-2 text-sm font-bold text-gray-600">
          Anuluj
        </button>
        <button
          type="button"
          disabled={save.isPending || membership.isLoading}
          onClick={() => save.mutate()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
        >
          Zapisz grupy
        </button>
      </div>
    </Modal>
  );
};

export default UserGroupsModal;
