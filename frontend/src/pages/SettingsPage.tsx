import { useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import DataTable from '@/components/ui/DataTable';
import SecurityGroupsPanel from '@/features/settings/SecurityGroupsPanel';
import UserFormModal from '@/features/settings/UserFormModal';
import UserGroupsModal from '@/features/settings/UserGroupsModal';
import { useMyPermissions, useSecurityGroups } from '@/hooks/usePermissions';
import { useTableControls } from '@/hooks/useTableControls';
import { useUsers } from '@/hooks/useUsers';
import { exportRowsToCsv } from '@/lib/csv';
import { useAuthStore } from '@/stores/authStore';
import type { Column } from '@/components/ui/DataTable';
import type { AdminUser, UserStatus } from '@/types';

const roleLabel = (status: UserStatus) => {
  if (status === 'admin') return 'Administrator';
  if (status === 'new_volunteer') return 'Nowy wolontariusz';
  return 'Użytkownik';
};

const SettingsPage = () => {
  const currentUser = useAuthStore((state) => state.user);
  const effective = useMyPermissions().data?.permissions ?? [];
  const canViewUsers = effective.includes('CAN_VIEW_USERS');
  const canManageUsers = effective.includes('CAN_MANAGE_USERS');
  const canViewSecurity = effective.includes('CAN_VIEW_SECURITY');
  const canManageSecurity = effective.includes('CAN_MANAGE_SECURITY');
  const [section, setSection] = useState<'users' | 'groups'>('users');
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [groupEditingUser, setGroupEditingUser] = useState<AdminUser | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'' | UserStatus>('');

  const closeForm = () => {
    setEditing(null);
    setIsAdding(false);
  };
  const { data, isLoading, save, remove } = useUsers({
    onSaved: closeForm,
    enabled: canViewUsers || canViewSecurity,
  });
  const security = useSecurityGroups(canViewSecurity);
  const users = data ?? [];
  const visibleSection = section === 'users' && canViewUsers ? 'users' : 'groups';
  const { search, setSearch, toggleSort, sortIcon, rows } = useTableControls(data, {
    searchFields: ['first_name', 'last_name', 'email', 'username', 'status'],
    initialSort: 'last_name',
    filterPredicate: (user) => !filterStatus || user.status === filterStatus,
  });

  const columns: Column<AdminUser>[] = [
    {
      id: 'name', header: 'Imię i nazwisko', sortKey: 'last_name',
      render: (user) => `${user.first_name} ${user.last_name}`.trim() || '-',
    },
    { id: 'email', header: 'Email', sortKey: 'email', render: (user) => user.email },
    { id: 'username', header: 'Login', sortKey: 'username', render: (user) => user.username },
    { id: 'status', header: 'Status konta', sortKey: 'status', render: (user) => roleLabel(user.status) },
    {
      id: 'actions', header: 'Akcje', align: 'center',
      render: (user) => (
        <div className="flex flex-wrap justify-center gap-2">
          {canManageSecurity && (
            <button type="button" onClick={() => setGroupEditingUser(user)} className="rounded bg-slate-600 px-3 py-1.5 text-xs font-bold text-white">
              Grupy
            </button>
          )}
          {canManageUsers && (
            <>
              <button type="button" onClick={() => setEditing(user)} className="rounded bg-indigo-500 px-3 py-1.5 text-xs font-bold text-white">Edytuj</button>
              <button
                type="button"
                disabled={user.id === currentUser?.id}
                onClick={() => confirm(`Usunąć użytkownika ${user.email}?`) && remove.mutate(user.id)}
                className="rounded bg-rose-500 px-3 py-1.5 text-xs font-bold text-white disabled:opacity-40"
              >
                Usuń
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  const exportUsers = () => exportRowsToCsv(
    'uzytkownicy.csv',
    [
      { header: 'Imię', value: (user) => user.first_name },
      { header: 'Nazwisko', value: (user) => user.last_name },
      { header: 'Email', value: (user) => user.email },
      { header: 'Login', value: (user) => user.username },
      { header: 'Status', value: (user) => roleLabel(user.status) },
    ],
    rows,
  );

  return (
    <PageShell>
      <div className="mb-6 flex flex-col gap-4 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold uppercase text-gray-900">Ustawienia</h1>
          <p className="mt-1 text-sm text-gray-500">Użytkownicy, grupy bezpieczeństwa i dziedziczone uprawnienia.</p>
        </div>
        {visibleSection === 'users' && canManageUsers && (
          <button type="button" onClick={() => setIsAdding(true)} className="rounded-lg bg-emerald-500 px-5 py-2 text-sm font-bold text-white">
            + Dodaj użytkownika
          </button>
        )}
      </div>

      <div className="mb-5 flex gap-2 border-b">
        {canViewUsers && (
          <button type="button" onClick={() => setSection('users')} className={`border-b-2 px-4 py-2 text-sm font-bold ${visibleSection === 'users' ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500'}`}>
            Użytkownicy
          </button>
        )}
        {canViewSecurity && (
          <button type="button" onClick={() => setSection('groups')} className={`border-b-2 px-4 py-2 text-sm font-bold ${visibleSection === 'groups' ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500'}`}>
            Grupy i uprawnienia
          </button>
        )}
      </div>

      {visibleSection === 'users' ? (
        <section>
          <div className="mb-4 grid gap-2 sm:grid-cols-2 xl:flex">
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Szukaj użytkownika…" className="h-10 rounded-lg border bg-gray-50 px-4 text-sm xl:flex-1" />
            <select value={filterStatus} onChange={(event) => setFilterStatus(event.target.value as '' | UserStatus)} className="h-10 rounded-lg border bg-gray-50 px-3 text-sm">
              <option value="">Wszystkie statusy</option>
              <option value="admin">Administratorzy</option>
              <option value="regular">Użytkownicy</option>
              <option value="new_volunteer">Nowi wolontariusze</option>
            </select>
            <button type="button" onClick={exportUsers} className="h-10 rounded-lg border px-4 text-sm font-bold text-gray-600">Eksport CSV</button>
          </div>
          <DataTable columns={columns} rows={rows} isLoading={isLoading} getRowKey={(user) => user.id} toggleSort={toggleSort} sortIcon={sortIcon} />
        </section>
      ) : canViewSecurity ? (
        <SecurityGroupsPanel users={users} canManage={canManageSecurity} />
      ) : (
        <p className="text-sm text-gray-500">Nie masz dostępu do ustawień bezpieczeństwa.</p>
      )}

      {(editing || isAdding) && (
        <UserFormModal user={editing} onClose={closeForm} onSave={save.mutate} isPending={save.isPending} />
      )}
      {groupEditingUser && (
        <UserGroupsModal user={groupEditingUser} groups={security.groups.data ?? []} onClose={() => setGroupEditingUser(null)} />
      )}
    </PageShell>
  );
};

export default SettingsPage;
