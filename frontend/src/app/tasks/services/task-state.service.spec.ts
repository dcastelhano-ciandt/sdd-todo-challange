import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { TaskStateService } from './task-state.service';
import type { Task } from '../../shared/models/task.model';

const TASK_PENDING: Task = {
  id: 'aaaaaaaa-0000-0000-0000-000000000001',
  userId: 'user-1',
  title: 'Buy groceries',
  completed: false,
};

const TASK_DONE: Task = {
  id: 'aaaaaaaa-0000-0000-0000-000000000002',
  userId: 'user-1',
  title: 'Clean house',
  completed: true,
};

describe('TaskStateService', () => {
  let service: TaskStateService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TaskStateService, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(TaskStateService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  describe('initial state', () => {
    it('should start with an empty tasks Signal', () => {
      expect(service.tasks()).toEqual([]);
    });

    it('should start with loading as false', () => {
      expect(service.loading()).toBe(false);
    });

    it('should start with filter as "all"', () => {
      expect(service.filter()).toBe('all');
    });
  });

  describe('loadTasks', () => {
    it('should set loading to true while the request is in-flight', () => {
      service.loadTasks().subscribe();

      expect(service.loading()).toBe(true);
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [] });
    });

    it('should set loading to false after the request completes', () => {
      service.loadTasks().subscribe();

      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });
      expect(service.loading()).toBe(false);
    });

    it('should populate the tasks Signal with data from the API', () => {
      service.loadTasks().subscribe();

      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING, TASK_DONE] });
      expect(service.tasks()).toEqual([TASK_PENDING, TASK_DONE]);
    });

    it('should set loading to false even when the request fails', () => {
      service.loadTasks().subscribe({ error: () => {} });

      httpTesting
        .expectOne('/api/v1/tasks')
        .flush({ detail: 'Server error' }, { status: 500, statusText: 'Internal Server Error' });

      expect(service.loading()).toBe(false);
    });

    it('should pass the filter value as a status query param when filter is not "all"', () => {
      service.filter.set('pending');
      service.loadTasks().subscribe();

      httpTesting.expectOne('/api/v1/tasks?status=pending').flush({ tasks: [TASK_PENDING] });
    });

    it('should not append a status query param when filter is "all"', () => {
      service.filter.set('all');
      service.loadTasks().subscribe();

      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [] });
    });
  });

  describe('createTask', () => {
    it('should POST the new task and add it to the tasks Signal', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_DONE] });

      service.createTask('Buy groceries').subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush(TASK_PENDING);

      expect(service.tasks()).toContain(TASK_PENDING);
    });

    it('should not update the tasks Signal on API error', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_DONE] });

      service.createTask('').subscribe({ error: () => {} });
      httpTesting
        .expectOne('/api/v1/tasks')
        .flush({ detail: 'title empty' }, { status: 422, statusText: 'Unprocessable Entity' });

      expect(service.tasks()).toEqual([TASK_DONE]);
    });
  });

  describe('updateTask', () => {
    it('should PUT the updated task and replace it in the tasks Signal', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });

      const updated = { ...TASK_PENDING, title: 'Buy milk' };
      service.updateTask(TASK_PENDING.id, 'Buy milk').subscribe();
      httpTesting.expectOne(`/api/v1/tasks/${TASK_PENDING.id}`).flush(updated);

      expect(service.tasks()).toEqual([updated]);
    });

    it('should not modify the tasks Signal on API error', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });

      service.updateTask(TASK_PENDING.id, '').subscribe({ error: () => {} });
      httpTesting
        .expectOne(`/api/v1/tasks/${TASK_PENDING.id}`)
        .flush({ detail: 'Forbidden' }, { status: 403, statusText: 'Forbidden' });

      expect(service.tasks()).toEqual([TASK_PENDING]);
    });
  });

  describe('toggleCompletion', () => {
    it('should apply an optimistic update before the API call resolves', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });

      service.toggleCompletion(TASK_PENDING.id).subscribe();

      // Optimistic update should already be reflected
      expect(service.tasks()[0].completed).toBe(true);

      const toggled = { ...TASK_PENDING, completed: true };
      httpTesting.expectOne(`/api/v1/tasks/${TASK_PENDING.id}/toggle`).flush(toggled);

      expect(service.tasks()[0].completed).toBe(true);
    });

    it('should rollback to the original snapshot on API error without re-fetching', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });

      service.toggleCompletion(TASK_PENDING.id).subscribe({ error: () => {} });

      // Optimistic update applied
      expect(service.tasks()[0].completed).toBe(true);

      httpTesting
        .expectOne(`/api/v1/tasks/${TASK_PENDING.id}/toggle`)
        .flush({ detail: 'Forbidden' }, { status: 403, statusText: 'Forbidden' });

      // Rolled back to original
      expect(service.tasks()).toEqual([TASK_PENDING]);
      // No extra GET should be made (httpTesting.verify() in afterEach ensures this)
    });

    it('should confirm the optimistic update with the server response', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });

      const toggled = { ...TASK_PENDING, completed: true };
      service.toggleCompletion(TASK_PENDING.id).subscribe();
      httpTesting.expectOne(`/api/v1/tasks/${TASK_PENDING.id}/toggle`).flush(toggled);

      expect(service.tasks()[0]).toEqual(toggled);
    });
  });

  describe('deleteTask', () => {
    it('should apply an optimistic removal before the API call resolves', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING, TASK_DONE] });

      service.deleteTask(TASK_PENDING.id).subscribe();

      // Optimistic removal should be reflected immediately
      expect(service.tasks()).toEqual([TASK_DONE]);

      httpTesting.expectOne(`/api/v1/tasks/${TASK_PENDING.id}`).flush({ message: 'Deleted' });

      expect(service.tasks()).toEqual([TASK_DONE]);
    });

    it('should rollback to the original snapshot on API error without re-fetching', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING, TASK_DONE] });

      service.deleteTask(TASK_PENDING.id).subscribe({ error: () => {} });

      // Optimistic removal applied
      expect(service.tasks()).toEqual([TASK_DONE]);

      httpTesting
        .expectOne(`/api/v1/tasks/${TASK_PENDING.id}`)
        .flush({ detail: 'Forbidden' }, { status: 403, statusText: 'Forbidden' });

      // Rolled back to original snapshot
      expect(service.tasks()).toEqual([TASK_PENDING, TASK_DONE]);
    });
  });
});

// ---------------------------------------------------------------------------
// Due Dates + Overdue Filter — TaskStateService extensions
// ---------------------------------------------------------------------------

/** Returns a date string N days from today (negative = past). */
function daysFromToday(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

const TASK_OVERDUE: Task = {
  id: 'overdue-001',
  userId: 'user-1',
  title: 'Overdue task',
  completed: false,
  due_date: daysFromToday(-1), // yesterday
};

const TASK_FUTURE: Task = {
  id: 'future-001',
  userId: 'user-1',
  title: 'Future task',
  completed: false,
  due_date: daysFromToday(5), // 5 days from now
};

const TASK_DONE_OVERDUE: Task = {
  id: 'done-overdue-001',
  userId: 'user-1',
  title: 'Completed past-due task',
  completed: true,
  due_date: daysFromToday(-2), // 2 days ago, but completed
};

const TASK_NO_DATE: Task = {
  id: 'nodate-001',
  userId: 'user-1',
  title: 'No due date',
  completed: false,
  due_date: null,
};

describe('TaskStateService — overdue derivation (tasks 8.1, 8.3)', () => {
  let service: TaskStateService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TaskStateService, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(TaskStateService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  describe('overdueCount signal', () => {
    it('should start at 0', () => {
      expect(service.overdueCount()).toBe(0);
    });

    it('should count past-due incomplete tasks', () => {
      service.loadTasks().subscribe();
      httpTesting
        .expectOne('/api/v1/tasks')
        .flush({ tasks: [TASK_OVERDUE, TASK_FUTURE, TASK_NO_DATE] });

      expect(service.overdueCount()).toBe(1);
    });

    it('should NOT count completed tasks even if past-due', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_OVERDUE, TASK_DONE_OVERDUE] });

      expect(service.overdueCount()).toBe(1); // only TASK_OVERDUE
    });

    it('should NOT count tasks without a due date', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_NO_DATE] });

      expect(service.overdueCount()).toBe(0);
    });

    it('should NOT count future-due tasks', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_FUTURE] });

      expect(service.overdueCount()).toBe(0);
    });

    it('should update overdueCount after toggleCompletion marks an overdue task as done', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_OVERDUE] });

      expect(service.overdueCount()).toBe(1);

      service.toggleCompletion(TASK_OVERDUE.id).subscribe();
      const toggled = { ...TASK_OVERDUE, completed: true };
      httpTesting.expectOne(`/api/v1/tasks/${TASK_OVERDUE.id}/toggle`).flush(toggled);

      expect(service.overdueCount()).toBe(0);
    });
  });

  describe('tasks() with filter "overdue"', () => {
    it('should return only past-due incomplete tasks when filter is "overdue"', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({
        tasks: [TASK_OVERDUE, TASK_FUTURE, TASK_DONE_OVERDUE, TASK_NO_DATE],
      });

      service.filter.set('overdue');

      const result = service.tasks();
      expect(result.length).toBe(1);
      expect(result[0].id).toBe(TASK_OVERDUE.id);
    });

    it('should return empty array when no overdue tasks exist', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({
        tasks: [TASK_FUTURE, TASK_DONE_OVERDUE, TASK_NO_DATE],
      });

      service.filter.set('overdue');

      expect(service.tasks()).toEqual([]);
    });

    it('should not include completed overdue tasks in overdue filter', () => {
      service.loadTasks().subscribe();
      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_DONE_OVERDUE] });

      service.filter.set('overdue');

      expect(service.tasks()).toEqual([]);
    });
  });
});

describe('TaskStateService — sort signals (task 8.2)', () => {
  let service: TaskStateService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TaskStateService, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(TaskStateService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should have sortBy defaulting to null', () => {
    expect(service.sortBy()).toBeNull();
  });

  it('should have sortDir defaulting to "asc"', () => {
    expect(service.sortDir()).toBe('asc');
  });

  it('should send sort_by and sort_dir params when sortBy is set', () => {
    service.sortBy.set('due_date');
    service.sortDir.set('asc');

    service.loadTasks().subscribe();
    httpTesting.expectOne('/api/v1/tasks?sort_by=due_date&sort_dir=asc').flush({ tasks: [] });
  });

  it('should send sort_by=due_date&sort_dir=desc when set', () => {
    service.sortBy.set('due_date');
    service.sortDir.set('desc');

    service.loadTasks().subscribe();
    httpTesting.expectOne('/api/v1/tasks?sort_by=due_date&sort_dir=desc').flush({ tasks: [] });
  });

  it('should NOT send sort params when sortBy is null', () => {
    service.sortBy.set(null);

    service.loadTasks().subscribe();
    httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [] });
  });
});

describe('TaskStateService — createTask and updateTask with dueDate (task 8.4)', () => {
  let service: TaskStateService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TaskStateService, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(TaskStateService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should POST with due_date when createTask is called with dueDate', () => {
    service.createTask('Buy milk', '2026-09-01').subscribe();

    const req = httpTesting.expectOne('/api/v1/tasks');
    expect(req.request.body).toEqual({ title: 'Buy milk', due_date: '2026-09-01' });
    req.flush({ ...TASK_PENDING, due_date: '2026-09-01' });
  });

  it('should PUT with due_date when updateTask is called with dueDate', () => {
    service.loadTasks().subscribe();
    httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });

    service.updateTask(TASK_PENDING.id, 'Updated title', '2026-10-01').subscribe();
    const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_PENDING.id}`);
    expect(req.request.body).toEqual({ title: 'Updated title', due_date: '2026-10-01' });
    req.flush({ ...TASK_PENDING, title: 'Updated title', due_date: '2026-10-01' });
  });

  it('should PUT with due_date: null to clear the due date', () => {
    service.loadTasks().subscribe();
    httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [TASK_PENDING] });

    service.updateTask(TASK_PENDING.id, 'Updated', null).subscribe();
    const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_PENDING.id}`);
    expect(req.request.body).toEqual({ title: 'Updated', due_date: null });
    req.flush({ ...TASK_PENDING, title: 'Updated', due_date: null });
  });
});
