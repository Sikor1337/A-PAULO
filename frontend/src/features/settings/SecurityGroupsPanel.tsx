import { useMemo, useState } from 'react';
import { useSecurityGroups } from '@/hooks/usePermissions';
import { useDialogs } from '@/components/ui/dialog/DialogProvider';
import HistoryButton from '@/features/audit/HistoryButton';
import type { AdminUser, PermissionCode } from '@/types';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';

interface Props {
  users: AdminUser[];
  canManage: boolean;
}

const SecurityGroupsPanel = ({ users, canManage }: Props) => {
  const { permissions, groups, create, save: saveGroup, remove } = useSecurityGroups();
  const { confirm, prompt } = useDialogs();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [drafts, setDrafts] = useState<Record<number, {
    name: string;
    description: string;
    permissionCodes: PermissionCode[];
    userIds: number[];
  }>>({});
  useUnsavedChanges(Object.keys(drafts).length > 0 && !saveGroup.isPending);

  const effectiveSelectedId = selectedId ?? groups.data?.[0]?.id ?? null;
  const selected = groups.data?.find((group) => group.id === effectiveSelectedId) ?? null;
  // PAP-95: STAFF permissions are admin-tunable; other system groups stay locked.
  const permissionsLocked = !!selected?.is_system && selected.system_key !== 'staff';
  const draft = selected
    ? drafts[selected.id] ?? {
      name: selected.name,
      description: selected.description,
      permissionCodes: selected.permissions.map((permission) => permission.code),
      userIds: selected.user_ids,
    }
    : null;
  const changeDraft = (change: Partial<NonNullable<typeof draft>>) => {
    if (!selected || !draft) return;
    setDrafts((current) => ({ ...current, [selected.id]: { ...draft, ...change } }));
  };

  const categories = useMemo(() => {
    const result = new Map<string, typeof permissions.data>();
    permissions.data?.forEach((permission) => {
      result.set(permission.category, [...(result.get(permission.category) ?? []), permission]);
    });
    return [...result.entries()];
  }, [permissions]);

  const addGroup = async () => {
    const groupName = await prompt({ title: 'Nowa grupa użytkowników', placeholder: 'Nazwa grupy', confirmLabel: 'Utwórz', required: true });
    if (!groupName) return;
    create.mutate(
      { name: groupName, description: '', permission_codes: [] },
      { onSuccess: (group) => setSelectedId(group.id) },
    );
  };

  const save = () => {
    if (!selected || !draft) return;
    saveGroup.mutate({
      id: selected.id,
      input: {
        name: draft.name.trim(),
        description: draft.description.trim(),
        permission_codes: draft.permissionCodes,
        user_ids: draft.userIds,
      },
    }, {
      onSuccess: () => setDrafts((current) => {
        const next = { ...current };
        delete next[selected.id];
        return next;
      }),
    });
  };

  return (
    <div className="grid gap-5 xl:grid-cols-[260px_1fr]">
      <aside className="rounded-xl border bg-gray-50 p-3">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-bold text-gray-800">Grupy użytkowników</h2>
          {canManage && (
            <button type="button" onClick={addGroup} className="rounded bg-emerald-500 px-2 py-1 text-xs font-bold text-white">+ Dodaj</button>
          )}
        </div>
        <div className="space-y-1">
          {groups.data?.map((group) => (
            <button
              key={group.id}
              type="button"
              onClick={() => setSelectedId(group.id)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm ${effectiveSelectedId === group.id ? 'bg-indigo-100 font-bold text-indigo-700' : 'hover:bg-white'}`}
            >
              {group.name}
              {group.is_system && <span className="ml-2 text-[10px] uppercase text-indigo-500">systemowa</span>}
            </button>
          ))}
        </div>
      </aside>

      {selected && draft ? (
        <section className="min-w-0 space-y-6">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm font-bold text-gray-700">
              Nazwa
              <input value={draft.name} disabled={selected.is_system || !canManage} onChange={(event) => changeDraft({ name: event.target.value })} className="mt-1 h-10 w-full rounded-lg border px-3 font-normal disabled:bg-gray-100" />
            </label>
            <label className="text-sm font-bold text-gray-700">
              Opis
              <input value={draft.description} disabled={selected.is_system || !canManage} onChange={(event) => changeDraft({ description: event.target.value })} className="mt-1 h-10 w-full rounded-lg border px-3 font-normal disabled:bg-gray-100" />
            </label>
          </div>

          <div>
            <h3 className="mb-2 font-bold text-gray-900">Matryca uprawnień</h3>
            {permissionsLocked && <p className="mb-3 text-xs text-amber-700">Zestaw uprawnień grupy systemowej jest chroniony przed zmianą.</p>}
            {selected.is_system && !permissionsLocked && <p className="mb-3 text-xs text-emerald-700">Grupa systemowa: nazwa i opis są chronione, ale uprawnienia można edytować.</p>}
            <div className="overflow-hidden rounded-xl border">
              {categories.map(([category, entries]) => (
                <div key={category} className="grid border-b last:border-b-0 md:grid-cols-[190px_1fr]">
                  <div className="bg-gray-50 px-4 py-3 text-sm font-bold text-gray-700">{category}</div>
                  <div className="grid gap-2 p-3 sm:grid-cols-2">
                    {entries?.map((permission) => (
                      <label key={permission.id} className="flex items-center gap-2 text-sm text-gray-700">
                        <input
                          type="checkbox"
                          disabled={permissionsLocked || !canManage}
                          checked={draft.permissionCodes.includes(permission.code)}
                          onChange={() => changeDraft({ permissionCodes: draft.permissionCodes.includes(permission.code)
                            ? draft.permissionCodes.filter((code) => code !== permission.code)
                            : [...draft.permissionCodes, permission.code] })}
                        />
                        {permission.name}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="mb-2 font-bold text-gray-900">Użytkownicy w grupie</h3>
            <div className="grid max-h-64 gap-2 overflow-y-auto rounded-xl border p-3 sm:grid-cols-2">
              {users.map((user) => (
                <label key={user.id} className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    disabled={!canManage}
                    checked={draft.userIds.includes(user.id)}
                    onChange={() => changeDraft({ userIds: draft.userIds.includes(user.id)
                      ? draft.userIds.filter((id) => id !== user.id)
                      : [...draft.userIds, user.id] })}
                  />
                  {`${user.first_name} ${user.last_name}`.trim() || user.email}
                </label>
              ))}
            </div>
          </div>

          {canManage && (
            <div className="flex flex-wrap justify-end gap-2">
              <HistoryButton
                path={`v1/security/groups/${selected.id}/audit`}
                entityName={`Grupa uprawnień: ${selected.name}`}
              />
              {!selected.is_system && (
                <button
                  type="button"
                  onClick={async () => { if (await confirm({ title: 'Usunąć grupę?', message: `Grupa „${selected.name}” zostanie usunięta.`, confirmLabel: 'Usuń' })) remove.mutate(selected.id); }}
                  className="rounded-lg bg-rose-100 px-4 py-2 text-sm font-bold text-rose-700"
                >
                  Usuń grupę
                </button>
              )}
              <button
                type="button"
                onClick={save}
                disabled={saveGroup.isPending}
                className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white disabled:cursor-wait disabled:opacity-50"
              >
                {saveGroup.isPending ? 'Zapisywanie…' : 'Zapisz zmiany'}
              </button>
            </div>
          )}
          {!canManage && (
            <div className="flex justify-end">
              <HistoryButton
                path={`v1/security/groups/${selected.id}/audit`}
                entityName={`Grupa uprawnień: ${selected.name}`}
              />
            </div>
          )}
        </section>
      ) : (
        <p className="text-sm text-gray-500">Wybierz grupę.</p>
      )}
    </div>
  );
};

export default SecurityGroupsPanel;
