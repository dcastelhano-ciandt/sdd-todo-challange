import { TestBed } from '@angular/core/testing';
import {
  provideHttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
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
      providers: [
        TaskStateService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
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

    // --- Search feature: q parameter forwarding ---

    it('should pass the q parameter to the API when loadTasks is called with a keyword', () => {
      service.filter.set('all');
      service.loadTasks('meeting').subscribe();

      httpTesting.expectOne('/api/v1/tasks?q=meeting').flush({ tasks: [] });
    });

    it('should pass both status and q when filter is not "all" and q is provided', () => {
      service.filter.set('pending');
      service.loadTasks('report').subscribe();

      httpTesting.expectOne('/api/v1/tasks?status=pending&q=report').flush({ tasks: [TASK_PENDING] });
    });

    it('should not append q param when loadTasks is called without a keyword', () => {
      service.filter.set('all');
      service.loadTasks().subscribe();

      httpTesting.expectOne('/api/v1/tasks').flush({ tasks: [] });
    });

    it('should read the filter signal at call time so filter changes are picked up', () => {
      service.filter.set('completed');
      service.loadTasks('test').subscribe();

      httpTesting.expectOne('/api/v1/tasks?status=completed&q=test').flush({ tasks: [TASK_DONE] });
    });

    it('should not reset the filter signal when q is provided', () => {
      service.filter.set('pending');
      service.loadTasks('keyword').subscribe();

      httpTesting.expectOne('/api/v1/tasks?status=pending&q=keyword').flush({ tasks: [] });

      // filter signal must remain unchanged
      expect(service.filter()).toBe('pending');
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
