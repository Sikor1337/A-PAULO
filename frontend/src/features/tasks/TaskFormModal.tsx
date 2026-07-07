import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import { useDepartmentList } from '@/hooks/useDepartments';
import { useVolunteerList } from '@/hooks/useVolunteers';
import { useQuery } from '@tanstack/react-query';
import { calendarService } from '@/services/calendarService';
import type { Task, TaskCreateInput } from '@/types';

interface TaskFormModalProps {
  task: Task | null;
  /** Preselected event id for the "add task from event" entry point. */
  initialEventId?: number | null;
  onClose: () => void;
  onSave: (args: { id?: number | null; data: TaskCreateInput }) => void;
  isPending: boolean;
}

/** Create/edit form for a task: dział, event, due date, assignees, checklist. */
const TaskFormModal = ({ task, initialEventId = null, onClose, onSave, isPending }: TaskFormModalProps) => {
  const [title, setTitle] = useState(task?.title ?? '');
  const [description, setDescription] = useState(task?.description ?? '');
  const [departmentId, setDepartmentId] = useState<number | ''>(task?.department_id ?? '');
  const [eventId, setEventId] = useState<number | ''>(task?.event_id ?? initialEventId ?? '');
  const [dueDate, setDueDate] = useState(task?.due_date ?? '');
  const [assigneeIds, setAssigneeIds] = useState<number[]>(
    task?.assignees.map((a) => a.volunteer_id) ?? [],
  );
  const [checklistText, setChecklistText] = useState('');

  const { data: departments } = useDepartmentList();
  const { data: volunteers } = useVolunteerList();
  const { data: events } = useQuery({
    queryKey: ['calendar-events-for-tasks'],
    queryFn: () => calendarService.getEvents({ sort: 'desc' }),
  });

  const toggleAssignee = (volunteerId: number) => {
    setAssigneeIds((current) =>
      current.includes(volunteerId)
        ? current.filter((id) => id !== volunteerId)
        : [...current, volunteerId],
    );
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!title.trim() || departmentId === '') return;
    onSave({
      id: task?.id ?? null,
      data: {
        title: title.trim(),
        description: description.trim(),
        department_id: departmentId,
        event_id: eventId === '' ? null : eventId,
        due_date: dueDate || null,
        assignee_ids: assigneeIds,
        checklist: task
          ? []
          : checklistText
              .split('\n')
              .map((line) => line.trim())
              .filter(Boolean),
        ...(task && eventId === '' ? { clear_event: true } : {}),
        ...(task && !dueDate ? { clear_due_date: true } : {}),
      } as TaskCreateInput,
    });
  };

  return (
    <Modal onClose={onClose} maxWidth="max-w-2xl">
      <div className="mb-6 flex items-start justify-between gap-4">
        <h2 className="text-xl font-bold text-gray-900">{task ? 'Edytuj zadanie' : 'Nowe zadanie'}</h2>
        <button onClick={onClose} className="text-2xl leading-none text-gray-400 hover:text-gray-600">
          &times;
        </button>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label htmlFor="task-title" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Tytuł *
          </label>
          <input
            id="task-title"
            type="text"
            value={title}
            required
            maxLength={200}
            onChange={(e) => setTitle(e.target.value)}
            className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
          />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label htmlFor="task-department" className="mb-1 block text-xs font-black uppercase text-gray-400">
              Dział *
            </label>
            <select
              id="task-department"
              value={departmentId}
              required
              onChange={(e) => setDepartmentId(e.target.value === '' ? '' : Number(e.target.value))}
              className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
            >
              <option value="">Wybierz dział...</option>
              {departments?.map((department) => (
                <option key={department.id} value={department.id}>
                  {department.icon} {department.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="task-event" className="mb-1 block text-xs font-black uppercase text-gray-400">
              Wydarzenie
            </label>
            <select
              id="task-event"
              value={eventId}
              onChange={(e) => setEventId(e.target.value === '' ? '' : Number(e.target.value))}
              className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
            >
              <option value="">Bez wydarzenia</option>
              {events?.map((event) => (
                <option key={event.id} value={event.id}>
                  {event.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="task-due" className="mb-1 block text-xs font-black uppercase text-gray-400">
              Termin
            </label>
            <input
              id="task-due"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="h-10 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm font-medium text-gray-600 outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label htmlFor="task-description" className="mb-1 block text-xs font-black uppercase text-gray-400">
            Opis
          </label>
          <textarea
            id="task-description"
            value={description}
            maxLength={5000}
            onChange={(e) => setDescription(e.target.value)}
            className="min-h-20 w-full resize-y rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
          />
        </div>

        <div>
          <p className="mb-1 text-xs font-black uppercase text-gray-400">Przypisani wolontariusze</p>
          <div className="max-h-40 space-y-1 overflow-y-auto rounded-lg border border-gray-200 p-2">
            {volunteers?.map((volunteer) => (
              <label key={volunteer.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={assigneeIds.includes(volunteer.id)}
                  onChange={() => toggleAssignee(volunteer.id)}
                />
                {volunteer.full_name}
              </label>
            ))}
          </div>
        </div>

        {!task && (
          <div>
            <label htmlFor="task-checklist" className="mb-1 block text-xs font-black uppercase text-gray-400">
              Checklista (jeden punkt na linię)
            </label>
            <textarea
              id="task-checklist"
              value={checklistText}
              placeholder={'Zamówić podest\nRozstawić nagłośnienie'}
              onChange={(e) => setChecklistText(e.target.value)}
              className="min-h-20 w-full resize-y rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium outline-none focus:border-indigo-500 focus:bg-white"
            />
          </div>
        )}

        <div className="flex flex-col-reverse gap-2 border-t pt-5 sm:flex-row sm:justify-end sm:gap-3">
          <button type="button" onClick={onClose} className="px-4 py-2 font-bold text-gray-400">
            Anuluj
          </button>
          <button
            type="submit"
            disabled={isPending || !title.trim() || departmentId === ''}
            className="min-h-10 rounded-lg bg-[#10b981] px-6 py-2 text-sm font-bold text-white transition-all hover:opacity-90 disabled:bg-gray-100 disabled:text-gray-300"
          >
            {isPending ? 'Zapisywanie...' : 'Zapisz'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default TaskFormModal;
