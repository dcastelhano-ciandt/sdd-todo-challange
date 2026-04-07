import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import type { Task, TaskStatus } from '../../shared/models/task.model';

interface TaskListResponse {
  tasks: Task[];
}

@Injectable({ providedIn: 'root' })
export class TaskApiService {
  private readonly http = inject(HttpClient);

  listTasks(status?: TaskStatus, q?: string): Observable<Task[]> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }
    if (q) {
      params = params.set('q', q);
    }
    return this.http
      .get<TaskListResponse>('/api/v1/tasks', { params })
      .pipe(map((response) => response.tasks));
  }

  createTask(title: string): Observable<Task> {
    return this.http.post<Task>('/api/v1/tasks', { title });
  }

  updateTask(taskId: string, title: string): Observable<Task> {
    return this.http.put<Task>(`/api/v1/tasks/${taskId}`, { title });
  }

  toggleCompletion(taskId: string): Observable<Task> {
    return this.http.patch<Task>(`/api/v1/tasks/${taskId}/toggle`, null);
  }

  deleteTask(taskId: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/tasks/${taskId}`);
  }
}
