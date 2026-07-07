export type TaskStatus = 'DO_ZROBIENIA' | 'W_TRAKCIE' | 'ZROBIONE';

export interface TaskChecklistItem {
  id: number;
  label: string;
  is_done: boolean;
  done_at: string | null;
  position: number;
}

export interface TaskAssignee {
  volunteer_id: number;
  full_name: string;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  status: TaskStatus;
  department_id: number;
  department_name: string | null;
  event_id: number | null;
  event_title: string | null;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  checklist: TaskChecklistItem[];
  assignees: TaskAssignee[];
  checklist_done: number;
  checklist_total: number;
}

export interface TaskCreateInput {
  title: string;
  description: string;
  department_id: number;
  event_id: number | null;
  due_date: string | null;
  assignee_ids: number[];
  checklist: string[];
}

export interface TaskUpdateInput {
  title?: string;
  description?: string;
  status?: TaskStatus;
  department_id?: number;
  event_id?: number | null;
  clear_event?: boolean;
  due_date?: string | null;
  clear_due_date?: boolean;
  assignee_ids?: number[];
}

export interface TaskFilters {
  departmentId: number | '';
  eventId: number | '';
  status: '' | TaskStatus;
}
