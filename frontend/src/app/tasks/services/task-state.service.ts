import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { TaskApiService } from './task-api.service';
import type { Task, TaskSortBy, TaskSortDir } from '../../shared/models/task.model';

/** Returns today's date as "YYYY-MM-DD" in local time. */
function todayISO(): string {
  const d = new Date();
  // Use local date parts to avoid UTC offset issues
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** Pure helper: a task is overdue when its due_date is in the past and it is incomplete. */
export function isOverdue(task: Task): boolean {
  return task.due_date != null && !task.completed && task.due_date < todayISO();
}

@Injectable({ providedIn: 'root' })
export class TaskStateService {
  private readonly taskApi = inject(TaskApiService);

  private readonly _tasks = signal<Task[]>([]);
  private readonly _loading = signal<boolean>(false);

  private readonly _allTasks = this._tasks.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly filter = signal<'all' | 'pending' | 'completed' | 'overdue'>('all');
  readonly sortBy = signal<TaskSortBy>(null);
  readonly sortDir = signal<TaskSortDir>('asc');

  readonly overdueCount = computed(() => this._allTasks().filter(isOverdue).length);

  readonly tasks = computed(() => {
    const f = this.filter();
    const all = this._allTasks();
    if (f === 'all') return all;
    if (f === 'completed') return all.filter((t) => t.completed);
    if (f === 'pending') return all.filter((t) => !t.completed);
    if (f === 'overdue') return all.filter(isOverdue);
    return all;
  });

  loadTasks(): Observable<void> {
    this._loading.set(true);

    const currentSortBy = this.sortBy();
    const currentSortDir = this.sortDir();

    // For 'pending' and 'completed' filters, pass status to the API for server-side filtering.
    // For 'all' and 'overdue' we load all tasks (overdue derivation is client-side).
    const filterValue = this.filter();
    let statusParam: import('../../shared/models/task.model').TaskStatus | undefined;
    if (filterValue === 'pending') statusParam = 'pending';
    else if (filterValue === 'completed') statusParam = 'completed';

    return this.taskApi.listTasks(statusParam, currentSortBy, currentSortDir).pipe(
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

  createTask(title: string, dueDate?: string | null): Observable<Task> {
    return this.taskApi.createTask(title, dueDate).pipe(
      tap((task) => {
        this._tasks.update((current) => [...current, task]);
      }),
    );
  }

  updateTask(taskId: string, title: string, dueDate?: string | null): Observable<Task> {
    return this.taskApi.updateTask(taskId, title, dueDate).pipe(
      tap((updated) => {
        this._tasks.update((current) => current.map((t) => (t.id === taskId ? updated : t)));
      }),
    );
  }

  toggleCompletion(taskId: string): Observable<Task> {
    const snapshot = this._tasks();

    // Optimistic update
    this._tasks.update((current) =>
      current.map((t) => (t.id === taskId ? { ...t, completed: !t.completed } : t)),
    );

    return this.taskApi.toggleCompletion(taskId).pipe(
      tap((updated) => {
        this._tasks.update((current) => current.map((t) => (t.id === taskId ? updated : t)));
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
