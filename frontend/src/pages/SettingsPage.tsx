import { useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import DataTable from '@/components/ui/DataTable';
import UserFormModal from '@/features/settings/UserFormModal';
import { useTableControls } from '@/hooks/useTableControls';
import { useUsers } from '@/hooks/useUsers';
import { exportRowsToCsv } from '@/lib/csv';
import { useAuthStore } from '@/stores/authStore';
import type { Column } from '@/components/ui/DataTable';
import type { AdminUser, UserStatus } from '@/types';

const roleLabel = (status: UserStatus) => (status === 'admin' ? 'Administrator' : 'Użytkownik');

const SettingsAdminPanel = () => {
  const currentUser = useAuthStore((state) => state.user);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'' | UserStatus>('');

  const closeForm = () => {
    setEditing(null);
    setIsAdding(false);
  };

  const { data, isLoading, save, remove } = useUsers({ onSaved: closeForm });
  const { search, setSearch, toggleSort, sortIcon, rows } = useTableControls(data, {
    searchFields: ['first_name', 'last_name', 'email', 'username', 'status'],
    initialSort: 'last_name',
    filterPredicate: (user) => {
      if (filterStatus && user.status !== filterStatus) return false;
      return true;
    },
  });

  const columns: Column<AdminUser>[] = [
    {
      id: 'name',
      header: 'Imię i nazwisko',
      widthClass: 'w-[22%]',
      sortKey: 'last_name',
      cellClassName: 'font-medium text-gray-800',
      render: (user) => `${user.first_name} ${user.last_name}`.trim() || '-',
    },
    {
      id: 'email',
      header: 'Email',
      widthClass: 'w-[24%]',
      sortKey: 'email',
      cellClassName: 'text-gray-500',
      render: (user) => user.email,
    },
    {
      id: 'username',
      header: 'Login',
      widthClass: 'w-[16%]',
      sortKey: 'username',
      cellClassName: 'text-gray-500',
      render: (user) => user.username,
    },
    {
      id: 'status',
      header: 'Rola',
      widthClass: 'w-[14%]',
      sortKey: 'status',
      render: (user) => (
        <span className={user.status === 'admin' ? 'font-bold text-indigo-700' : 'text-gray-600'}>
          {roleLabel(user.status)}
        </span>
      ),
    },
    {
      id: 'is_active',
      header: 'Status',
      widthClass: 'w-[10%]',
      align: 'center',
      sortKey: 'is_active',
      render: (user) => (
        <span className={user.is_active ? 'text-emerald-600 font-bold' : 'text-gray-400 font-bold'}>
          {user.is_active ? 'Aktywny' : 'Wyłączony'}
        </span>
      ),
    },
    {
      id: 'actions',
      header: 'Akcje',
      widthClass: 'w-[14%] min-w-[120px]',
      align: 'center',
      render: (user) => (
        <div className="flex justify-center gap-2">
          <button
            type="button"
            onClick={() => setEditing(user)}
            className="bg-[#6366f1] text-white px-3 py-1.5 rounded text-xs font-bold hover:opacity-90"
          >
            Edytuj
          </button>
          <button
            type="button"
            disabled={user.id === currentUser?.id}
            onClick={() => {
              if (confirm(`Usunąć użytkownika ${user.email}?`)) remove.mutate(user.id);
            }}
            className="bg-[#ef4444] text-white px-3 py-1.5 rounded text-xs font-bold hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Usuń
          </button>
        </div>
      ),
    },
  ];

  const exportUsers = () => {
    exportRowsToCsv(
      'uzytkownicy.csv',
      [
        { header: 'Imię', value: (user) => user.first_name },
        { header: 'Nazwisko', value: (user) => user.last_name },
        { header: 'Email', value: (user) => user.email },
        { header: 'Login', value: (user) => user.username },
        { header: 'Rola', value: (user) => roleLabel(user.status) },
        { header: 'Aktywny', value: (user) => (user.is_active ? 'TAK' : 'NIE') },
      ],
      rows,
    );
  };

  return (
    <>
      <div className="flex items-center justify-between gap-4 mb-6 border-b pb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Ustawienia</h1>
          <p className="text-sm text-gray-500 mt-1">Użytkownicy aplikacji i ich uprawnienia.</p>
        </div>
        <button
          type="button"
          onClick={() => setIsAdding(true)}
          className="bg-[#10b981] text-white px-5 py-2 rounded-lg font-bold text-sm hover:opacity-90"
        >
          + Dodaj użytkownika
        </button>
      </div>

      <div className="grid grid-cols-[220px_1fr] gap-6">
        <aside className="border-r pr-4">
          <button
            type="button"
            className="w-full text-left px-3 py-2 rounded-md bg-[#eef2ff] text-indigo-700 text-sm font-bold"
          >
            Użytkownicy
          </button>
        </aside>

        <section>
          <div className="mb-4 flex gap-2 items-center">
            <input
              type="text"
              placeholder="Szukaj po imieniu, nazwisku, emailu lub loginie..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1 px-4 h-10 border border-gray-200 rounded-lg bg-gray-50 focus:bg-white focus:border-indigo-500 outline-none text-sm font-medium"
            />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as '' | UserStatus)}
              className="h-10 px-3 border border-gray-200 rounded-lg bg-gray-50 focus:border-indigo-500 outline-none text-sm font-medium text-gray-600 min-w-[150px]"
            >
              <option value="">Wszystkie role</option>
              <option value="admin">Administratorzy</option>
              <option value="regular">Użytkownicy</option>
            </select>
            <button
              type="button"
              onClick={exportUsers}
              className="h-10 px-4 border border-gray-200 rounded-lg text-sm font-bold text-gray-600 hover:bg-gray-50"
            >
              Eksport CSV
            </button>
          </div>

          <DataTable
            columns={columns}
            rows={rows}
            isLoading={isLoading}
            getRowKey={(user) => user.id}
            toggleSort={toggleSort}
            sortIcon={sortIcon}
          />
        </section>
      </div>

      {(editing || isAdding) && (
        <UserFormModal user={editing} onClose={closeForm} onSave={save.mutate} isPending={save.isPending} />
      )}
    </>
  );
};

const SettingsPage = () => {
  const currentUser = useAuthStore((state) => state.user);

  if (currentUser?.role !== 'admin') {
    return (
      <PageShell>
        <div className="max-w-xl">
          <h1 className="text-xl font-bold text-gray-900 uppercase mb-2">Ustawienia</h1>
          <p className="text-sm text-gray-500">Ta sekcja jest dostępna tylko dla administratorów.</p>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <SettingsAdminPanel />
    </PageShell>
  );
};

export default SettingsPage;
