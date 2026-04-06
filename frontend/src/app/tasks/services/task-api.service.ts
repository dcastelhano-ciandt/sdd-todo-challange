import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import type { Task, TaskStatus, TaskSortBy, TaskSortDir } from '../../shared/models/task.model';

interface TaskListResponse {
  tasks: Task[];
}

@Injectable({ providedIn: 'root' })
export class TaskApiService {
  private readonly http = inject(HttpClient);

  listTasks(
    status?: TaskStatus,
    sortBy?: TaskSortBy,
    sortDir?: TaskSortDir,
  ): Observable<Task[]> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }
    if (sortBy) {
      params = params.set('sort_by', sortBy);
      params = params.set('sort_dir', sortDir ?? 'asc');
    }
    return this.http
      .get<TaskListResponse>('/api/v1/tasks', { params })
      .pipe(map((response) => response.tasks));
  }

  createTask(title: string, dueDate?: string | null): Observable<Task> {
    const body: Record<string, unknown> = { title };
    if (dueDate !== undefined) {
      body['due_date'] = dueDate;
    }
    return this.http.post<Task>('/api/v1/tasks', body);
  }

  updateTask(taskId: string, title: string, dueDate?: string | null): Observable<Task> {
    const body: Record<string, unknown> = { title };
    if (dueDate !== undefined) {
      body['due_date'] = dueDate;
    }
    return this.http.put<Task>(`/api/v1/tasks/${taskId}`, body);
  }

  toggleCompletion(taskId: string): Observable<Task> {
    return this.http.patch<Task>(`/api/v1/tasks/${taskId}/toggle`, null);
  }

  deleteTask(taskId: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/tasks/${taskId}`);
  }
}
