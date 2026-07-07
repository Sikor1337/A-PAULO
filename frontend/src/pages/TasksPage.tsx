import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import PageShell from '@/components/layout/PageShell';
import TaskFormModal from '@/features/tasks/TaskFormModal';
import { useDepartmentList } from '@/hooks/useDepartments';
import { useVolunteerList } from '@/hooks/useVolunteers';
import { useTaskActions, useTaskList } from '@/hooks/useTasks';
import { useHasPermission } from '@/hooks/usePermissions';
import { formatDate } from '@/lib/date';
import type { Task, TaskStatus } from '@/types';

const STATUS_OPTIONS: TaskStatus[] = ['DO_ZROBIENIA', 'W_TRAKCIE', 'ZROBIONE'];

const STATUS_STYLES: Record<TaskStatus, string> = {
  DO_ZROBIENIA: 'bg-blue-100 text-blue-700',
  W_TRAKCIE: 'bg-amber-100 text-amber-700',
  ZROBIONE: 'bg-emerald-100 text-emerald-700',
};

const statusLabel = (status: TaskStatus) => status.replace(/_/g, ' ');

const TasksPage: React.FC = () => {
  const { hasPermission: canManage } = useHasPermission('CAN_MANAGE_TASKS');
  const [searchParams, setSearchParams] = useSearchParams();
  // Derived live from the URL, so sidebar navigation to plain /tasks clears it.
  const filterEvent: number | '' = Number(searchParams.get('event')) || '';

  const [filterDepartment, setFilterDepartment] = useState<number | ''>('');
  const [filterStatus, setFilterStatus] = useState<'' | TaskStatus>('');
  const [filterVolunteer, setFilterVolunteer] = useState<number | ''>('');
  const [editing, setEditing] = useState<Task | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [newItemDrafts, setNewItemDrafts] = useState<Record<number, string>>({});

  const closeForm = () => {
    setEditing(null);
    setIsAdding(false);
  };
  const { data: departments } = useDepartmentList();
  const { data: volunteers } = useVolunteerList();
  const { data: tasks, isLoading } = useTaskList({
    departmentId: filterDepartment,
    eventId: filterEvent,
    status: filterStatus,
    volunteerId: filterVolunteer,
  });
  const { save, remove, addItem, updateItem, removeItem } = useTaskActions({ onSaved: closeForm });

  const submitNewItem = (task: Task) => {
    const label = (newItemDrafts[task.id] ?? '').trim();
    if (!label) return;
    addItem.mutate(
      { taskId: task.id, label },
      { onSuccess: () => setNewItemDrafts((current) => ({ ...current, [task.id]: '' })) },
    );
  };

  return (
    <PageShell>
      <div className="mb-6 flex flex-col gap-4 border-b pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📋</span>
          <h1 className="text-xl font-bold text-gray-900 uppercase">Zadania</h1>
        </div>
        {canManage && (
          <button
            onClick={() => setIsAdding(true)}
            className="flex min-h-10 items-center justify-center gap-2 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white transition-all hover:opacity-90"
          >
            + Dodaj zadanie
          </button>
        )}
      </div>

      <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:flex lg:items-center">
        <select
          value={filterDepartment}
          onChange={(e) => setFilterDepartment(e.target.value === '' ? '' : Number(e.target.value))}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 lg:w-auto lg:min-w-[180px]"
        >
          <option value="">Wszystkie działy</option>
          {departments?.map((department) => (
            <option key={department.id} value={department.id}>
              {department.icon} {department.name}
            </option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as '' | TaskStatus)}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 lg:w-auto lg:min-w-[160px]"
        >
          <option value="">Wszystkie statusy</option>
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {statusLabel(status)}
            </option>
          ))}
        </select>
        <select
          value={filterVolunteer}
          onChange={(e) => setFilterVolunteer(e.target.value === '' ? '' : Number(e.target.value))}
          className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500 lg:w-auto lg:min-w-[200px]"
        >
          <option value="">Wszyscy wolontariusze</option>
          {volunteers?.map((volunteer) => (
            <option key={volunteer.id} value={volunteer.id}>
              {volunteer.full_name}
            </option>
          ))}
        </select>
        {filterEvent !== '' && (
          <span className="flex h-10 items-center gap-2 rounded-lg bg-indigo-50 px-3 text-sm font-bold text-indigo-700">
            Filtr: wydarzenie #{filterEvent}
            <button
              type="button"
              onClick={() => setSearchParams({})}
              className="text-lg leading-none text-indigo-400 hover:text-indigo-700"
              aria-label="Usuń filtr wydarzenia"
            >
              &times;
            </button>
          </span>
        )}
      </div>

      {isLoading ? (
        <p className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">Ładowanie...</p>
      ) : !tasks?.length ? (
        <p className="rounded-lg border border-gray-200 p-8 text-center text-sm font-medium text-gray-400">Brak zadań</p>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => {
            const progress = task.checklist_total
              ? Math.round((task.checklist_done / task.checklist_total) * 100)
              : null;
            return (
              <div key={task.id} className="rounded-lg border border-gray-200 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-bold text-gray-900">{task.title}</p>
                    <p className="mt-1 text-xs font-medium text-gray-400">
                      🗂️ {task.department_name ?? '—'}
                      {task.event_title && <> · 📅 {task.event_title}</>}
                      {task.due_date && <> · ⏰ termin: {formatDate(task.due_date)}</>}
                      {task.completed_at && <> · ✅ wykonano: {formatDate(task.completed_at)}</>}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {canManage ? (
                      <select
                        value={task.status}
                        disabled={save.isPending}
                        onChange={(e) => save.mutate({ id: task.id, data: { status: e.target.value as TaskStatus } })}
                        className="h-9 rounded-lg border border-gray-200 bg-gray-50 px-2 text-xs font-bold text-gray-600 outline-none focus:border-indigo-500"
                      >
                        {STATUS_OPTIONS.map((status) => (
                          <option key={status} value={status}>
                            {statusLabel(status)}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className={`rounded px-2 py-0.5 text-[11px] font-bold ${STATUS_STYLES[task.status]}`}>
                        {statusLabel(task.status)}
                      </span>
                    )}
                    {canManage && (
                      <>
                        <button
                          type="button"
                          onClick={() => setEditing(task)}
                          className="min-h-9 rounded-md bg-indigo-50 px-3 text-xs font-bold text-indigo-700 transition-colors hover:bg-indigo-100"
                        >
                          ✏️
                        </button>
                        <button
                          type="button"
                          disabled={remove.isPending}
                          onClick={() => {
                            if (!confirm(`Usunąć zadanie „${task.title}”?`)) return;
                            remove.mutate(task.id);
                          }}
                          className="min-h-9 rounded-md bg-rose-50 px-3 text-xs font-bold text-rose-700 transition-colors hover:bg-rose-100 disabled:opacity-50"
                        >
                          🗑️
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {task.description && (
                  <p className="mt-2 whitespace-pre-wrap text-sm font-medium text-gray-700">{task.description}</p>
                )}

                {!!task.assignees.length && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {task.assignees.map((assignee) => (
                      <span key={assignee.volunteer_id} className="rounded bg-indigo-50 px-2 py-0.5 text-[11px] font-bold text-indigo-700">
                        🙋 {assignee.full_name}
                      </span>
                    ))}
                  </div>
                )}

                {progress !== null && (
                  <div className="mt-3">
                    <div className="mb-1 flex items-center justify-between text-xs font-bold text-gray-500">
                      <span>Postęp: {task.checklist_done}/{task.checklist_total}</span>
                      <span>{progress}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                      <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${progress}%` }} />
                    </div>
                  </div>
                )}

                {(task.checklist.length > 0 || canManage) && (
                  <div className="mt-3 space-y-1">
                    {task.checklist.map((item) => (
                      <div key={item.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={item.is_done}
                          disabled={!canManage || updateItem.isPending}
                          onChange={(e) =>
                            updateItem.mutate({ taskId: task.id, itemId: item.id, data: { is_done: e.target.checked } })
                          }
                        />
                        <span className={`flex-1 font-medium ${item.is_done ? 'text-gray-400 line-through' : 'text-gray-700'}`}>
                          {item.label}
                        </span>
                        {item.done_at && <span className="text-[10px] font-medium text-gray-400">{formatDate(item.done_at)}</span>}
                        {canManage && (
                          <button
                            type="button"
                            onClick={() => removeItem.mutate({ taskId: task.id, itemId: item.id })}
                            className="px-1 text-gray-300 hover:text-rose-500"
                            aria-label="Usuń punkt"
                          >
                            &times;
                          </button>
                        )}
                      </div>
                    ))}
                    {canManage && (
                      <div className="flex gap-2 pt-1">
                        <input
                          type="text"
                          maxLength={300}
                          placeholder="Nowy punkt checklisty..."
                          value={newItemDrafts[task.id] ?? ''}
                          onChange={(e) => setNewItemDrafts((current) => ({ ...current, [task.id]: e.target.value }))}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              submitNewItem(task);
                            }
                          }}
                          className="h-9 flex-1 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
                        />
                        <button
                          type="button"
                          disabled={addItem.isPending || !(newItemDrafts[task.id] ?? '').trim()}
                          onClick={() => submitNewItem(task)}
                          className="min-h-9 rounded-lg bg-indigo-600 px-3 text-xs font-bold text-white transition-all hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
                        >
                          Dodaj
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {canManage && (editing || isAdding) && (
        <TaskFormModal
          task={editing}
          initialEventId={filterEvent === '' ? null : filterEvent}
          onClose={closeForm}
          onSave={save.mutate}
          isPending={save.isPending}
        />
      )}
    </PageShell>
  );
};

export default TasksPage;
