import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { TaskApiService } from './task-api.service';
import type { Task, TaskStatus } from '../../shared/models/task.model';

@Injectable({ providedIn: 'root' })
export class TaskStateService {
  private readonly taskApi = inject(TaskApiService);

  private readonly _tasks = signal<Task[]>([]);
  private readonly _loading = signal<boolean>(false);

  readonly tasks = this._tasks.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly filter = signal<'all' | 'pending' | 'completed'>('all');

  loadTasks(): Observable<void> {
    this._loading.set(true);
    const currentFilter = this.filter();
    const status: TaskStatus | undefined =
      currentFilter === 'all' ? undefined : currentFilter;

    return this.taskApi.listTasks(status).pipe(
      tap((tasks) => {
        this._tasks.set(tasks);
        this._loading.set(false);
      }),
      catchError((err) => {
        this._loading.set(false);
        return throwError(() => err);
      }),
    ) as unknown as Observable<void>;
  }

  createTask(title: string): Observable<Task> {
    return this.taskApi.createTask(title).pipe(
      tap((task) => {
        this._tasks.update((current) => [...current, task]);
      }),
    );
  }

  updateTask(taskId: string, title: string): Observable<Task> {
    return this.taskApi.updateTask(taskId, title).pipe(
      tap((updated) => {
        this._tasks.update((current) =>
          current.map((t) => (t.id === taskId ? updated : t)),
        );
      }),
    );
  }

  toggleCompletion(taskId: string): Observable<Task> {
    const snapshot = this._tasks();

    // Optimistic update
    this._tasks.update((current) =>
      current.map((t) =>
        t.id === taskId ? { ...t, completed: !t.completed } : t,
      ),
    );

    return this.taskApi.toggleCompletion(taskId).pipe(
      tap((updated) => {
        this._tasks.update((current) =>
          current.map((t) => (t.id === taskId ? updated : t)),
        );
      }),
      catchError((err) => {
        // Rollback to the original snapshot
        this._tasks.set(snapshot);
        return throwError(() => err);
      }),
    );
  }

  deleteTask(taskId: string): Observable<void> {
    const snapshot = this._tasks();

    // Optimistic removal
    this._tasks.update((current) => current.filter((t) => t.id !== taskId));

    return this.taskApi.deleteTask(taskId).pipe(
      catchError((err) => {
        // Rollback to the original snapshot
        this._tasks.set(snapshot);
        return throwError(() => err);
      }),
    );
  }
}
