import { TestBed } from '@angular/core/testing';
import {
  HttpClient,
  provideHttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { TaskApiService } from './task-api.service';
import type { Task } from '../../shared/models/task.model';

const TASK_A: Task = {
  id: 'aaaaaaaa-0000-0000-0000-000000000001',
  userId: 'bbbbbbbb-0000-0000-0000-000000000001',
  title: 'Buy groceries',
  completed: false,
};

const TASK_B: Task = {
  id: 'aaaaaaaa-0000-0000-0000-000000000002',
  userId: 'bbbbbbbb-0000-0000-0000-000000000001',
  title: 'Clean house',
  completed: true,
};

describe('TaskApiService', () => {
  let service: TaskApiService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        TaskApiService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(TaskApiService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  describe('listTasks', () => {
    it('should GET /api/v1/tasks without a status filter', () => {
      service.listTasks().subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });

    it('should GET /api/v1/tasks?status=pending when filter is pending', () => {
      service.listTasks('pending').subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks?status=pending');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });

    it('should GET /api/v1/tasks?status=completed when filter is completed', () => {
      service.listTasks('completed').subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks?status=completed');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });

    it('should return the tasks array from the response', () => {
      let result: Task[] | undefined;
      service.listTasks().subscribe((tasks) => {
        result = tasks;
      });

      const req = httpTesting.expectOne('/api/v1/tasks');
      req.flush({ tasks: [TASK_A, TASK_B] });

      expect(result).toEqual([TASK_A, TASK_B]);
    });

    // --- Search feature: q parameter ---

    it('should append ?q=report when listTasks is called with q="report"', () => {
      service.listTasks(undefined, 'report').subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks?q=report');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });

    it('should append both status and q when both are provided', () => {
      service.listTasks('pending', 'report').subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks?status=pending&q=report');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });

    it('should not append q param when q is empty string', () => {
      service.listTasks(undefined, '').subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });

    it('should not append q param when q is undefined', () => {
      service.listTasks(undefined, undefined).subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });

    it('should append only q when status is undefined and q is provided', () => {
      service.listTasks(undefined, 'groceries').subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks?q=groceries');
      expect(req.request.method).toBe('GET');
      req.flush({ tasks: [] });
    });
  });

  describe('createTask', () => {
    it('should POST to /api/v1/tasks with the title', () => {
      service.createTask('New task').subscribe();

      const req = httpTesting.expectOne('/api/v1/tasks');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ title: 'New task' });
      req.flush(TASK_A);
    });

    it('should return the created Task', () => {
      let result: Task | undefined;
      service.createTask('Buy groceries').subscribe((task) => {
        result = task;
      });

      const req = httpTesting.expectOne('/api/v1/tasks');
      req.flush(TASK_A);

      expect(result).toEqual(TASK_A);
    });

    it('should propagate HTTP errors to the caller', () => {
      let errorReceived = false;
      service.createTask('').subscribe({ error: () => { errorReceived = true; } });

      const req = httpTesting.expectOne('/api/v1/tasks');
      req.flush({ detail: 'title too short' }, { status: 422, statusText: 'Unprocessable Entity' });

      expect(errorReceived).toBe(true);
    });
  });

  describe('updateTask', () => {
    it('should PUT to /api/v1/tasks/:id with the new title', () => {
      service.updateTask(TASK_A.id, 'Updated title').subscribe();

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual({ title: 'Updated title' });
      req.flush({ ...TASK_A, title: 'Updated title' });
    });

    it('should return the updated Task', () => {
      const updated = { ...TASK_A, title: 'Updated' };
      let result: Task | undefined;
      service.updateTask(TASK_A.id, 'Updated').subscribe((task) => {
        result = task;
      });

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}`);
      req.flush(updated);

      expect(result).toEqual(updated);
    });

    it('should propagate 403 errors to the caller', () => {
      let errorReceived = false;
      service.updateTask(TASK_A.id, 'Steal').subscribe({ error: () => { errorReceived = true; } });

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}`);
      req.flush({ detail: 'Forbidden' }, { status: 403, statusText: 'Forbidden' });

      expect(errorReceived).toBe(true);
    });
  });

  describe('toggleCompletion', () => {
    it('should PATCH to /api/v1/tasks/:id/toggle', () => {
      service.toggleCompletion(TASK_A.id).subscribe();

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}/toggle`);
      expect(req.request.method).toBe('PATCH');
      req.flush({ ...TASK_A, completed: true });
    });

    it('should send an empty body', () => {
      service.toggleCompletion(TASK_A.id).subscribe();

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}/toggle`);
      expect(req.request.body).toBeNull();
      req.flush({ ...TASK_A, completed: true });
    });

    it('should return the updated Task', () => {
      const toggled = { ...TASK_A, completed: true };
      let result: Task | undefined;
      service.toggleCompletion(TASK_A.id).subscribe((task) => {
        result = task;
      });

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}/toggle`);
      req.flush(toggled);

      expect(result).toEqual(toggled);
    });

    it('should propagate 404 errors to the caller', () => {
      let errorReceived = false;
      service.toggleCompletion('non-existent').subscribe({ error: () => { errorReceived = true; } });

      const req = httpTesting.expectOne('/api/v1/tasks/non-existent/toggle');
      req.flush({ detail: 'Not found' }, { status: 404, statusText: 'Not Found' });

      expect(errorReceived).toBe(true);
    });
  });

  describe('deleteTask', () => {
    it('should DELETE /api/v1/tasks/:id', () => {
      service.deleteTask(TASK_A.id).subscribe();

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}`);
      expect(req.request.method).toBe('DELETE');
      req.flush({ message: 'Task deleted' });
    });

    it('should complete without a value on success', () => {
      let completed = false;
      service.deleteTask(TASK_A.id).subscribe({ complete: () => { completed = true; } });

      const req = httpTesting.expectOne(`/api/v1/tasks/${TASK_A.id}`);
      req.flush({ message: 'Task deleted' });

      expect(completed).toBe(true);
    });

    it('should propagate 404 errors to the caller', () => {
      let errorReceived = false;
      service.deleteTask('missing-id').subscribe({ error: () => { errorReceived = true; } });

      const req = httpTesting.expectOne('/api/v1/tasks/missing-id');
      req.flush({ detail: 'Not found' }, { status: 404, statusText: 'Not Found' });

      expect(errorReceived).toBe(true);
    });
  });
});
