import { useMemo, useState } from 'react';
import PageShell from '@/components/layout/PageShell';
import DepartmentFormModal from '@/features/departments/DepartmentFormModal';
import { useDepartmentActions, useDepartmentDetail, useDepartmentList } from '@/hooks/useDepartments';
import { useVolunteerList } from '@/hooks/useVolunteers';
import { useHasPermission } from '@/hooks/usePermissions';
import { useAuthStore } from '@/stores/authStore';
import { formatDate } from '@/lib/date';
import type { DepartmentListItem } from '@/types';

const DepartmentsPage: React.FC = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_DEPARTMENTS');
  const user = useAuthStore((state) => state.user);
  const [showArchived, setShowArchived] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editing, setEditing] = useState<DepartmentListItem | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [newMemberId, setNewMemberId] = useState<number | ''>('');

  const { data: departments, isLoading } = useDepartmentList(showArchived);
  const { data: detail } = useDepartmentDetail(selectedId);
  const { data: volunteers } = useVolunteerList();
  const closeForm = () => {
    setEditing(null);
    setIsAdding(false);
  };
  const { save, addMember, removeMember, join, approveMember, leave } = useDepartmentActions({ onSaved: closeForm });

  // The current user's own membership in the selected department, if any.
  const myMembership = useMemo(() => {
    const email = user?.email?.toLowerCase();
    if (!email || !detail) return null;
    return detail.members.find((member) => member.email.toLowerCase() === email) ?? null;
  }, [detail, user?.email]);

  // Auto-select first department once the list arrives (condition turns false after set)
  if (departments?.length && selectedId === null) {
    setSelectedId(departments[0].id);
  }
  // Selected department disappeared from the filtered list — fall back to the first one
  if (departments?.length && selectedId !== null && !departments.some((d) => d.id === selectedId)) {
    setSelectedId(departments[0].id);
  }

  const availableVolunteers = useMemo(() => {
    if (!volunteers || !detail) return [];
    const memberIds = new Set(detail.members.map((m) => m.volunteer_id));
    return volunteers.filter((v) => !memberIds.has(v.id));
  }, [volunteers, detail]);

  const toggleArchive = () => {
    if (!detail) return;
    const question = detail.is_archived
      ? `Przywrócić dział „${detail.name}”?`
      : `Zarchiwizować dział „${detail.name}”? Dane i historia zostaną zachowane.`;
    if (!confirm(question)) return;
    save.mutate({ id: detail.id, data: { is_archived: !detail.is_archived } });
  };

  const submitNewMember = () => {
    if (!detail || newMemberId === '') return;
    addMember.mutate(
      { id: detail.id, volunteerId: newMemberId },
      { onSuccess: () => setNewMemberId('') },
    );
  };

  return (
    <PageShell>
      <div className="mb-6 flex flex-col gap-4 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🗂️</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Działy</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex min-h-10 cursor-pointer items-center gap-2 rounded-lg border border-gray-200 px-3 text-sm font-bold text-gray-600">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            Pokaż zarchiwizowane
          </label>
          {canManage && (
            <button
              onClick={() => setIsAdding(true)}
              className="flex min-h-10 items-center justify-center gap-2 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white transition-all hover:opacity-90"
            >
              + Dodaj dział
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        {/* ── Sub-menu: departments one under another ── */}
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
                onClick={() => setSelectedId(department.id)}
                className={`flex min-h-11 w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-all ${
                  selectedId === department.id
                    ? 'bg-indigo-50 font-semibold text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="w-6 shrink-0 text-center">{department.icon || '🗂️'}</span>
                <span className="min-w-0 flex-1 truncate text-sm">{department.name}</span>
                {department.is_archived && (
                  <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-bold text-gray-500">ARCH.</span>
                )}
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-bold text-gray-500">
                  {department.member_count}
                </span>
              </button>
            ))
          )}
        </nav>

        {/* ── Selected department workspace ── */}
        <div>
          {!detail ? (
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
                      className="min-h-9 rounded-lg bg-emerald-50 px-3 text-xs font-bold text-emerald-700 transition-colors hover:bg-emerald-100 disabled:opacity-50"
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
                        if (!confirm('Opuścić ten dział?')) return;
                        leave.mutate(detail.id);
                      }}
                      className="min-h-9 rounded-lg bg-rose-50 px-3 text-xs font-bold text-rose-700 transition-colors hover:bg-rose-100 disabled:opacity-50"
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
                        className="min-h-9 rounded-lg bg-indigo-50 px-3 text-xs font-bold text-indigo-700 transition-colors hover:bg-indigo-100"
                      >
                        ✏️ Edytuj
                      </button>
                      <button
                        type="button"
                        onClick={toggleArchive}
                        disabled={save.isPending}
                        className="min-h-9 rounded-lg bg-amber-50 px-3 text-xs font-bold text-amber-700 transition-colors hover:bg-amber-100 disabled:opacity-50"
                      >
                        {detail.is_archived ? '↩️ Przywróć' : '🗄️ Archiwizuj'}
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Tabs — only Członkowie in v1; more tools arrive in later tickets */}
              <div className="mb-4 border-b">
                <span className="inline-block border-b-2 border-indigo-500 px-4 py-2 text-sm font-bold text-indigo-700">
                  Członkowie ({detail.members.length})
                </span>
              </div>

              {canManage && !detail.is_archived && (
                <div className="mb-4 flex flex-col gap-2 sm:flex-row">
                  <select
                    value={newMemberId}
                    onChange={(e) => setNewMemberId(e.target.value === '' ? '' : Number(e.target.value))}
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
                    className="min-h-10 rounded-lg bg-[#10b981] px-4 text-sm font-bold text-white transition-all hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
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
                                <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">OCZEKUJE</span>
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
                                    onClick={() => approveMember.mutate({ id: detail.id, volunteerId: member.volunteer_id })}
                                    className="min-h-9 rounded-md bg-emerald-50 px-3 text-xs font-bold text-emerald-700 transition-colors hover:bg-emerald-100 disabled:opacity-50"
                                  >
                                    Zatwierdź
                                  </button>
                                )}
                                <button
                                  type="button"
                                  disabled={removeMember.isPending}
                                  onClick={() => {
                                    if (!confirm(`Usunąć ${member.full_name} z działu?`)) return;
                                    removeMember.mutate({ id: detail.id, volunteerId: member.volunteer_id });
                                  }}
                                  className="min-h-9 rounded-md bg-rose-50 px-3 text-xs font-bold text-rose-700 transition-colors hover:bg-rose-100 disabled:opacity-50"
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
    </PageShell>
  );
};

export default DepartmentsPage;
