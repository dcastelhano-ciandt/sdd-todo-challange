export interface Task {
  id: string;
  userId: string;
  title: string;
  completed: boolean;
  due_date?: string | null;
}

export interface CreateTaskRequest {
  title: string;
  due_date?: string | null;
}

export interface UpdateTaskRequest {
  title: string;
  due_date?: string | null;
}

export type TaskStatus = 'pending' | 'completed';
export type TaskSortDir = 'asc' | 'desc';
export type TaskSortBy = 'due_date' | null;
