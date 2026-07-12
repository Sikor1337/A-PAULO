import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import PageShell from '@/components/layout/PageShell';
import DepartmentFormModal from '@/features/departments/DepartmentFormModal';
import DepartmentInventoryModal from '@/features/departments/DepartmentInventoryModal';
import {
  useDepartmentActions,
  useDepartmentDetail,
  useDepartmentInventory,
  useDepartmentInventoryActions,
  useDepartmentList,
} from '@/hooks/useDepartments';
import { useHasPermission } from '@/hooks/usePermissions';
import { useTaskList } from '@/hooks/useTasks';
import { useVolunteerList } from '@/hooks/useVolunteers';
import { appDialog } from '@/lib/appDialog';
import { formatDate } from '@/lib/date';
import { parseApiError } from '@/lib/errors';
import { useAuthStore } from '@/stores/authStore';
import type {
  DepartmentInventoryItem,
  DepartmentInventoryItemInput,
  DepartmentListItem,
  TaskStatus,
} from '@/types';

type DepartmentTab = 'members' | 'tasks' | 'inventory';

const STATUS_STYLES: Record<TaskStatus, string> = {
  DO_ZROBIENIA: 'bg-blue-100 text-blue-700',
  W_TRAKCIE: 'bg-amber-100 text-amber-700',
  ZROBIONE: 'bg-emerald-100 text-emerald-700',
};

const statusLabel = (status: TaskStatus) => status.replace(/_/g, ' ');

const DepartmentsPage: React.FC = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_DEPARTMENTS');
  const { hasPermission: canViewTasks } = useHasPermission('CAN_VIEW_TASKS');
  const user = useAuthStore((state) => state.user);
  const [showArchived, setShowArchived] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<DepartmentTab>('members');
  const [editing, setEditing] = useState<DepartmentListItem | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [newMemberId, setNewMemberId] = useState<number | ''>('');
  const [inventoryModalItem, setInventoryModalItem] = useState<
    DepartmentInventoryItem | null | undefined
  >(undefined);

  const { data: departments, isLoading } = useDepartmentList(showArchived);
  const activeSelectedId = departments?.some((department) => department.id === selectedId)
    ? selectedId
    : departments?.[0]?.id ?? null;
  const detailQuery = useDepartmentDetail(activeSelectedId);
  const { data: detail } = detailQuery;
  const inventoryQuery = useDepartmentInventory(activeSelectedId);
  const taskQuery = useTaskList(
    { departmentId: activeSelectedId ?? '' },
    canViewTasks && activeSelectedId !== null,
  );
  const { data: volunteers = [] } = useVolunteerList();

  const closeForm = () => {
    setEditing(null);
    setIsAdding(false);
  };
  const { save, addMember, removeMember, join, approveMember, leave } =
    useDepartmentActions({ onSaved: closeForm });
  const inventoryActions = useDepartmentInventoryActions();

  const myMembership = useMemo(() => {
    const email = user?.email?.toLowerCase();
    if (!email || !detail) return null;
    return detail.members.find((member) => member.email.toLowerCase() === email) ?? null;
  }, [detail, user?.email]);

  const availableVolunteers = useMemo(() => {
    if (!detail) return [];
    const memberIds = new Set(detail.members.map((member) => member.volunteer_id));
    return volunteers.filter((volunteer) => !memberIds.has(volunteer.id));
  }, [volunteers, detail]);

  const toggleArchive = async () => {
    if (!detail) return;
    const restoring = detail.is_archived;
    const confirmed = await appDialog.confirm(
      restoring
        ? `Przywrócić dział „${detail.name}”?`
        : `Zarchiwizować dział „${detail.name}”? Dane i historia zostaną zachowane.`,
      {
        title: restoring ? 'Przywróć dział' : 'Archiwizuj dział',
        confirmLabel: restoring ? 'Przywróć' : 'Archiwizuj',
        tone: 'warning',
      },
    );
    if (confirmed) save.mutate({ id: detail.id, data: { is_archived: !detail.is_archived } });
  };

  const submitNewMember = () => {
    if (!detail || newMemberId === '') return;
    addMember.mutate(
      { id: detail.id, volunteerId: newMemberId },
      { onSuccess: () => setNewMemberId('') },
    );
  };

  const saveInventoryItem = (data: DepartmentInventoryItemInput) => {
    if (!detail || inventoryModalItem === undefined) return;
    inventoryActions.save.mutate(
      {
        departmentId: detail.id,
        itemId: inventoryModalItem?.id,
        data,
      },
      { onSuccess: () => setInventoryModalItem(undefined) },
    );
  };

  const deleteInventoryItem = async (item: DepartmentInventoryItem) => {
    if (!detail) return;
    const confirmed = await appDialog.confirm(`Usunąć przedmiot „${item.name}”?`, {
      title: 'Usuń przedmiot',
      confirmLabel: 'Usuń',
      tone: 'error',
    });
    if (confirmed) {
      inventoryActions.remove.mutate({ departmentId: detail.id, itemId: item.id });
    }
  };

  return (
    <PageShell>
      <div className="mb-6 flex flex-col gap-4 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🗂️</span>
          <h1 className="text-xl font-bold uppercase text-gray-900">Działy</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex min-h-10 cursor-pointer items-center gap-2 rounded-lg border border-gray-200 px-3 text-sm font-bold text-gray-600">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(event) => setShowArchived(event.target.checked)}
            />
            Pokaż zarchiwizowane
          </label>
          {canManage && (
            <button
              type="button"
              onClick={() => setIsAdding(true)}
              className="flex min-h-10 items-center justify-center gap-2 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white hover:opacity-90"
            >
              + Dodaj dział
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <nav className="space-y-1 lg:border-r lg:pr-4" aria-label="Lista działów">
          {isLoading ? (
            <p className="p-4 text-sm font-medium text-gray-400">Ładowanie...</p>
          ) : !departments?.length ? (
            <p className="p-4 text-sm font-medium text-gray-400">Brak działów</p>
          ) : (
            departments.map((department) => (
              <button
                key={department.id}
                type="button"
                onClick={() => {
                  setSelectedId(department.id);
                  setInventoryModalItem(undefined);
                }}
                className={`flex min-h-11 w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-all ${
                  activeSelectedId === department.id
                    ? 'bg-indigo-50 font-semibold text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="w-6 shrink-0 text-center">{department.icon || '🗂️'}</span>
                <span className="min-w-0 flex-1 truncate text-sm">{department.name}</span>
                {department.is_archived && (
                  <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-bold text-gray-500">
                    ARCH.
                  </span>
                )}
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-bold text-gray-500">
                  {department.member_count}
                </span>
              </button>
            ))
          )}
        </nav>

        <div>
          {detailQuery.isLoading ? (
            <p className="p-8 text-center text-sm font-medium text-gray-400">Ładowanie działu...</p>
          ) : detailQuery.isError ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center">
              <p className="text-sm font-semibold text-rose-700">
                {parseApiError(detailQuery.error, 'Nie udało się pobrać szczegółów działu.')}
              </p>
              <button
                type="button"
                onClick={() => detailQuery.refetch()}
                className="mt-4 rounded-lg bg-rose-600 px-4 py-2 text-sm font-bold text-white"
              >
                Spróbuj ponownie
              </button>
            </div>
          ) : !detail ? (
            <p className="p-8 text-center text-sm font-medium text-gray-400">Wybierz dział z listy</p>
          ) : (
            <>
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                    <span>{detail.icon || '🗂️'}</span>
                    {detail.name}
                    {detail.is_archived && (
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                        ZARCHIWIZOWANY
                      </span>
                    )}
                  </h2>
                  {detail.description && (
                    <p className="mt-1 text-sm font-medium text-gray-500">{detail.description}</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {!detail.is_archived && !myMembership && (
                    <button
                      type="button"
                      disabled={join.isPending}
                      onClick={() => join.mutate(detail.id)}
                      className="min-h-9 rounded-lg bg-emerald-50 px-3 text-xs font-bold text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
                    >
                      ➕ Dołącz
                    </button>
                  )}
                  {myMembership?.membership_status === 'PENDING' && (
                    <span className="inline-flex min-h-9 items-center rounded-lg bg-amber-50 px-3 text-xs font-bold text-amber-700">
                      ⏳ Prośba oczekuje na akceptację
                    </span>
                  )}
                  {myMembership?.membership_status === 'ACTIVE' && (
                    <button
                      type="button"
                      disabled={leave.isPending}
                      onClick={async () => {
                        const confirmed = await appDialog.confirm('Opuścić ten dział?', {
                          title: 'Opuść dział',
                          confirmLabel: 'Opuść',
                          tone: 'warning',
                        });
                        if (confirmed) leave.mutate(detail.id);
                      }}
                      className="min-h-9 rounded-lg bg-rose-50 px-3 text-xs font-bold text-rose-700 hover:bg-rose-100 disabled:opacity-50"
                    >
                      🚪 Opuść dział
                    </button>
                  )}
                  {canManage && (
                    <>
                      <button
                        type="button"
                        onClick={() =>
                          setEditing({
                            id: detail.id,
                            name: detail.name,
                            icon: detail.icon,
                            description: detail.description,
                            is_archived: detail.is_archived,
                            member_count: detail.members.length,
                          })
                        }
                        className="min-h-9 rounded-lg bg-indigo-50 px-3 text-xs font-bold text-indigo-700 hover:bg-indigo-100"
                      >
                        ✏️ Edytuj
                      </button>
                      <button
                        type="button"
                        onClick={toggleArchive}
                        disabled={save.isPending}
                        className="min-h-9 rounded-lg bg-amber-50 px-3 text-xs font-bold text-amber-700 hover:bg-amber-100 disabled:opacity-50"
                      >
                        {detail.is_archived ? '↩️ Przywróć' : '🗄️ Archiwizuj'}
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="mb-4 flex gap-1 overflow-x-auto border-b" role="tablist">
                {(
                  [
                    ['members', `Członkowie (${detail.members.length})`],
                    ['tasks', `Zadania (${taskQuery.data?.length ?? 0})`],
                    ['inventory', `Magazyn (${inventoryQuery.data?.length ?? 0})`],
                  ] as const
                ).map(([tab, label]) => (
                  <button
                    key={tab}
                    type="button"
                    role="tab"
                    aria-selected={activeTab === tab}
                    onClick={() => setActiveTab(tab)}
                    className={`whitespace-nowrap border-b-2 px-4 py-2 text-sm font-bold ${
                      activeTab === tab
                        ? 'border-indigo-500 text-indigo-700'
                        : 'border-transparent text-gray-500 hover:text-gray-800'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {activeTab === 'members' && (
                <section aria-label="Członkowie działu">
                  {canManage && !detail.is_archived && (
                    <div className="mb-4 flex flex-col gap-2 sm:flex-row">
                      <select
                        value={newMemberId}
                        onChange={(event) =>
                          setNewMemberId(event.target.value === '' ? '' : Number(event.target.value))
                        }
                        className="h-10 flex-1 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
                      >
                        <option value="">Wybierz wolontariusza...</option>
                        {availableVolunteers.map((volunteer) => (
                          <option key={volunteer.id} value={volunteer.id}>
                            {volunteer.full_name} ({volunteer.email})
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        disabled={newMemberId === '' || addMember.isPending}
                        onClick={submitNewMember}
                        className="min-h-10 rounded-lg bg-[#10b981] px-4 text-sm font-bold text-white hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
                      >
                        {addMember.isPending ? 'Dodawanie...' : '+ Dodaj członka'}
                      </button>
                    </div>
                  )}

                  {detail.members.length === 0 ? (
                    <p className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">
                      Ten dział nie ma jeszcze członków
                    </p>
                  ) : (
                    <div className="overflow-x-auto rounded-lg border border-gray-200">
                      <table className="w-full min-w-[520px] border-collapse text-left text-sm">
                        <thead>
                          <tr className="bg-[#1e2330] text-[10px] font-bold uppercase tracking-widest text-white">
                            <th className="px-3 py-3">Imię i nazwisko</th>
                            <th className="px-3 py-3">Email</th>
                            <th className="px-3 py-3">Status</th>
                            <th className="px-3 py-3">W dziale od</th>
                            {canManage && <th className="px-3 py-3 text-center">Akcje</th>}
                          </tr>
                        </thead>
                        <tbody>
                          {detail.members.map((member) => (
                            <tr key={member.id} className="border-b border-gray-100 last:border-0 hover:bg-amber-50/40">
                              <td className="px-3 py-3 font-bold text-gray-900">
                                <span className="flex items-center gap-2">
                                  {member.full_name}
                                  {member.membership_status === 'PENDING' && (
                                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">
                                      OCZEKUJE
                                    </span>
                                  )}
                                </span>
                              </td>
                              <td className="px-3 py-3 font-medium text-gray-600">{member.email}</td>
                              <td className="px-3 py-3 font-semibold text-gray-600">{member.status}</td>
                              <td className="px-3 py-3 font-medium text-gray-500">{formatDate(member.created_at)}</td>
                              {canManage && (
                                <td className="px-3 py-3 text-center">
                                  <div className="flex justify-center gap-2">
                                    {member.membership_status === 'PENDING' && (
                                      <button
                                        type="button"
                                        disabled={approveMember.isPending}
                                        onClick={() =>
                                          approveMember.mutate({
                                            id: detail.id,
                                            volunteerId: member.volunteer_id,
                                          })
                                        }
                                        className="min-h-9 rounded-md bg-emerald-50 px-3 text-xs font-bold text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
                                      >
                                        Zatwierdź
                                      </button>
                                    )}
                                    <button
                                      type="button"
                                      disabled={removeMember.isPending}
                                      onClick={async () => {
                                        const confirmed = await appDialog.confirm(
                                          `Usunąć ${member.full_name} z działu?`,
                                          {
                                            title: 'Usuń osobę z działu',
                                            confirmLabel: 'Usuń',
                                            tone: 'error',
                                          },
                                        );
                                        if (confirmed) {
                                          removeMember.mutate({
                                            id: detail.id,
                                            volunteerId: member.volunteer_id,
                                          });
                                        }
                                      }}
                                      className="min-h-9 rounded-md bg-rose-50 px-3 text-xs font-bold text-rose-700 hover:bg-rose-100 disabled:opacity-50"
                                    >
                                      Usuń
                                    </button>
                                  </div>
                                </td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              )}

              {activeTab === 'tasks' && (
                <section aria-label="Zadania działu">
                  {canViewTasks && (
                    <div className="mb-4 flex justify-end">
                      <Link
                        to={`/tasks?department=${detail.id}`}
                        className="rounded-lg bg-indigo-50 px-4 py-2 text-sm font-bold text-indigo-700 hover:bg-indigo-100"
                      >
                        Otwórz pełną listę zadań
                      </Link>
                    </div>
                  )}
                  {!canViewTasks ? (
                    <p className="rounded-lg border p-8 text-center text-sm text-gray-500">
                      Nie masz uprawnienia do przeglądania zadań.
                    </p>
                  ) : taskQuery.isLoading ? (
                    <p className="rounded-lg border p-8 text-center text-sm text-gray-400">Ładowanie...</p>
                  ) : taskQuery.isError ? (
                    <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-center">
                      <p className="text-sm font-semibold text-rose-700">
                        {parseApiError(taskQuery.error, 'Nie udało się pobrać zadań działu.')}
                      </p>
                      <button
                        type="button"
                        onClick={() => taskQuery.refetch()}
                        className="mt-3 rounded-lg bg-rose-600 px-4 py-2 text-sm font-bold text-white"
                      >
                        Spróbuj ponownie
                      </button>
                    </div>
                  ) : !taskQuery.data?.length ? (
                    <p className="rounded-lg border p-8 text-center text-sm text-gray-400">Brak zadań w tym dziale</p>
                  ) : (
                    <div className="space-y-3">
                      {taskQuery.data.map((task) => (
                        <article key={task.id} className="rounded-lg border border-gray-200 p-4">
                          <div className="flex flex-wrap items-start justify-between gap-2">
                            <div>
                              <h3 className="font-bold text-gray-900">{task.title}</h3>
                              <p className="mt-1 text-xs font-medium text-gray-500">
                                {task.due_date ? `Termin: ${formatDate(task.due_date)}` : 'Bez terminu'}
                              </p>
                            </div>
                            <span className={`rounded px-2 py-1 text-[11px] font-bold ${STATUS_STYLES[task.status]}`}>
                              {statusLabel(task.status)}
                            </span>
                          </div>
                          {task.description && (
                            <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700">{task.description}</p>
                          )}
                          <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold text-gray-500">
                            <span>Lista: {task.checklist_done}/{task.checklist_total}</span>
                            <span>•</span>
                            <span>
                              Odpowiedzialni: {task.assignees.map((person) => person.full_name).join(', ') || 'brak'}
                            </span>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {activeTab === 'inventory' && (
                <section aria-label="Magazyn działu">
                  {!detail.is_archived && (
                    <div className="mb-4 flex justify-end">
                      <button
                        type="button"
                        onClick={() => setInventoryModalItem(null)}
                        className="rounded-lg bg-[#10b981] px-4 py-2 text-sm font-bold text-white hover:opacity-90"
                      >
                        + Dodaj przedmiot
                      </button>
                    </div>
                  )}
                  {inventoryQuery.isLoading ? (
                    <p className="rounded-lg border p-8 text-center text-sm text-gray-400">Ładowanie...</p>
                  ) : inventoryQuery.isError ? (
                    <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-center">
                      <p className="text-sm font-semibold text-rose-700">
                        {parseApiError(inventoryQuery.error, 'Nie udało się pobrać magazynu działu.')}
                      </p>
                      <button
                        type="button"
                        onClick={() => inventoryQuery.refetch()}
                        className="mt-3 rounded-lg bg-rose-600 px-4 py-2 text-sm font-bold text-white"
                      >
                        Spróbuj ponownie
                      </button>
                    </div>
                  ) : !inventoryQuery.data?.length ? (
                    <p className="rounded-lg border p-8 text-center text-sm text-gray-400">Magazyn jest pusty</p>
                  ) : (
                    <div className="overflow-x-auto rounded-lg border border-gray-200">
                      <table className="w-full min-w-[720px] border-collapse text-left text-sm">
                        <thead>
                          <tr className="bg-[#1e2330] text-[10px] font-bold uppercase tracking-widest text-white">
                            <th className="px-3 py-3">Nazwa przedmiotu</th>
                            <th className="px-3 py-3">Miejsce znajdowania</th>
                            <th className="px-3 py-3">Wziął</th>
                            <th className="px-3 py-3">Data pobrania</th>
                            <th className="px-3 py-3 text-center">Akcje</th>
                          </tr>
                        </thead>
                        <tbody>
                          {inventoryQuery.data.map((item) => (
                            <tr key={item.id} className="border-b border-gray-100 last:border-0">
                              <td className="px-3 py-3 font-bold text-gray-900">{item.name}</td>
                              <td className="px-3 py-3 text-gray-600">{item.location}</td>
                              <td className="px-3 py-3 text-gray-600">
                                {item.borrowed_by_volunteer_name ?? '—'}
                              </td>
                              <td className="px-3 py-3 text-gray-500">
                                {item.borrowed_at ? formatDate(item.borrowed_at) : '—'}
                              </td>
                              <td className="px-3 py-3 text-center">
                                <div className="flex justify-center gap-2">
                                  {!detail.is_archived && (
                                    <button
                                      type="button"
                                      onClick={() => setInventoryModalItem(item)}
                                      className="min-h-9 rounded-md bg-indigo-50 px-3 text-xs font-bold text-indigo-700 hover:bg-indigo-100"
                                    >
                                      Edytuj
                                    </button>
                                  )}
                                  {canManage && (
                                    <button
                                      type="button"
                                      disabled={inventoryActions.remove.isPending}
                                      onClick={() => deleteInventoryItem(item)}
                                      className="min-h-9 rounded-md bg-rose-50 px-3 text-xs font-bold text-rose-700 hover:bg-rose-100 disabled:opacity-50"
                                    >
                                      Usuń
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              )}
            </>
          )}
        </div>
      </div>

      {canManage && (editing || isAdding) && (
        <DepartmentFormModal
          department={editing}
          onClose={closeForm}
          onSave={save.mutate}
          isPending={save.isPending}
        />
      )}
      {inventoryModalItem !== undefined && (
        <DepartmentInventoryModal
          item={inventoryModalItem}
          volunteers={volunteers}
          isPending={inventoryActions.save.isPending}
          onClose={() => setInventoryModalItem(undefined)}
          onSave={saveInventoryItem}
        />
      )}
    </PageShell>
  );
};

export default DepartmentsPage;
