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

const roleLabel = (status: UserStatus) => {
  if (status === 'admin') return 'Administrator';
  if (status === 'new_volunteer') return 'Nowy wolontariusz';
  return 'Użytkownik';
};

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
      <div className="mb-6 flex flex-col gap-4 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Ustawienia</h1>
          <p className="text-sm text-gray-500 mt-1">Użytkownicy aplikacji i ich uprawnienia.</p>
        </div>
        <button
          type="button"
          onClick={() => setIsAdding(true)}
          className="min-h-10 rounded-lg bg-[#10b981] px-5 py-2 text-sm font-bold text-white hover:opacity-90"
        >
          + Dodaj użytkownika
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[220px_1fr] lg:gap-6">
        <aside className="border-b pb-3 lg:border-b-0 lg:border-r lg:pb-0 lg:pr-4">
          <button
            type="button"
            className="w-full text-left px-3 py-2 rounded-md bg-[#eef2ff] text-indigo-700 text-sm font-bold"
          >
            Użytkownicy
          </button>
        </aside>

        <section className="min-w-0">
          <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2 xl:flex xl:items-center">
            <input
              type="text"
              placeholder="Szukaj po imieniu, nazwisku, emailu lub loginie..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-4 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white xl:flex-1"
            />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as '' | UserStatus)}
              className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 xl:w-auto xl:min-w-[150px]"
            >
              <option value="">Wszystkie role</option>
              <option value="admin">Administratorzy</option>
              <option value="regular">Użytkownicy</option>
              <option value="new_volunteer">Nowi wolontariusze</option>
            </select>
            <button
              type="button"
              onClick={exportUsers}
              className="h-10 rounded-lg border border-gray-200 px-4 text-sm font-bold text-gray-600 hover:bg-gray-50 sm:col-span-2 xl:col-span-1"
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

  if (currentUser?.status !== 'admin') {
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
