import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import type { Task, TaskStatus, TaskSortBy, TaskSortDir } from '../../shared/models/task.model';
import { environment } from '../../../environments/environment';

interface TaskListResponse {
  tasks: Task[];
}

@Injectable({ providedIn: 'root' })
export class TaskApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl || '';

  // Overloads to support both call patterns:
  // (status, sortBy, sortDir) and (status, q, sortBy, sortDir)
  listTasks(status?: TaskStatus, sortBy?: TaskSortBy, sortDir?: TaskSortDir): Observable<Task[]>;
  listTasks(
    status?: TaskStatus,
    q?: string,
    sortBy?: TaskSortBy,
    sortDir?: TaskSortDir,
  ): Observable<Task[]>;
  listTasks(status?: TaskStatus, a?: any, b?: any, c?: any): Observable<Task[]> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }
    // Detect whether second arg is q or sortBy
    // Treat null same as undefined for overload resolution
    const isSortBySecond = a === 'due_date' || a == null;
    const q = isSortBySecond ? undefined : (a as string | undefined);
    const sortBy =
      (isSortBySecond ? (a as TaskSortBy | undefined) : (b as TaskSortBy | undefined)) ?? undefined;
    const sortDir =
      (isSortBySecond ? (b as TaskSortDir | undefined) : (c as TaskSortDir | undefined)) ??
      undefined;

    if (q) {
      params = params.set('q', q);
    }
    if (sortBy === 'due_date') {
      params = params.set('sort_by', 'due_date');
      params = params.set('sort_dir', sortDir ?? 'asc');
    }
    return this.http
      .get<TaskListResponse>(`${this.base}/api/v1/tasks`, { params })
      .pipe(map((response) => response.tasks));
  }

  createTask(title: string, dueDate?: string | null): Observable<Task> {
    const body: Record<string, unknown> = { title };
    if (dueDate !== undefined) {
      body['due_date'] = dueDate;
    }
    return this.http.post<Task>(`${this.base}/api/v1/tasks`, body);
  }

  updateTask(taskId: string, title: string, dueDate?: string | null): Observable<Task> {
    const body: Record<string, unknown> = { title };
    if (dueDate !== undefined) {
      body['due_date'] = dueDate;
    }
    return this.http.put<Task>(`${this.base}/api/v1/tasks/${taskId}`, body);
  }

  toggleCompletion(taskId: string): Observable<Task> {
    return this.http.patch<Task>(`${this.base}/api/v1/tasks/${taskId}/toggle`, null);
  }

  deleteTask(taskId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/api/v1/tasks/${taskId}`);
  }
}
