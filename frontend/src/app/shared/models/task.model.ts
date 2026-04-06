export interface Task {
  id: string;
  userId: string;
  title: string;
  completed: boolean;
}

export interface CreateTaskRequest {
  title: string;
}

export interface UpdateTaskRequest {
  title: string;
}

export type TaskStatus = 'pending' | 'completed';
