import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { TaskListComponent } from './task-list.component';
import { TaskStateService } from '../services/task-state.service';
import { signal } from '@angular/core';
import type { Task } from '../../shared/models/task.model';
import { Observable, of } from 'rxjs';

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

function createMockTaskStateService(overrides: Partial<{
  tasks: Task[];
  loading: boolean;
  filter: 'all' | 'pending' | 'completed';
  loadTasksFn: () => Observable<void>;
}> = {}) {
  const tasksSignal = signal<Task[]>(overrides.tasks ?? []);
  const loadingSignal = signal<boolean>(overrides.loading ?? false);
  const filterSignal = signal<'all' | 'pending' | 'completed'>(overrides.filter ?? 'all');

  return {
    tasks: tasksSignal.asReadonly(),
    loading: loadingSignal.asReadonly(),
    filter: filterSignal,
    loadTasks: overrides.loadTasksFn ?? (() => of(undefined as unknown as void)),
    _tasksSignal: tasksSignal,
    _loadingSignal: loadingSignal,
  };
}

describe('TaskListComponent', () => {
  let component: TaskListComponent;
  let fixture: ReturnType<typeof TestBed.createComponent<TaskListComponent>>;

  describe('with real TaskStateService', () => {
    let httpTesting: HttpTestingController;
    let taskState: TaskStateService;

    beforeEach(() => {
      TestBed.configureTestingModule({
        imports: [TaskListComponent],
        providers: [
          provideHttpClient(),
          provideHttpClientTesting(),
        ],
      });

      fixture = TestBed.createComponent(TaskListComponent);
      component = fixture.componentInstance;
      taskState = TestBed.inject(TaskStateService);
      httpTesting = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
      httpTesting.verify();
    });

    it('should call TaskStateService.loadTasks on ngOnInit', () => {
      const loadTasksSpy = vi.spyOn(taskState, 'loadTasks').mockReturnValue(of(undefined as unknown as void));
      fixture.detectChanges();

      expect(loadTasksSpy).toHaveBeenCalledOnce();
    });
  });

  describe('with mocked TaskStateService — loading state', () => {
    let mockState: ReturnType<typeof createMockTaskStateService>;

    beforeEach(() => {
      mockState = createMockTaskStateService({ loading: true });

      TestBed.configureTestingModule({
        imports: [TaskListComponent],
        providers: [
          { provide: TaskStateService, useValue: mockState },
        ],
      });

      fixture = TestBed.createComponent(TaskListComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should display a loading indicator when loading is true', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="loading-indicator"]')).not.toBeNull();
    });

    it('should not display the task list while loading', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="task-list"]')).toBeNull();
    });
  });

  describe('with mocked TaskStateService — empty state', () => {
    let mockState: ReturnType<typeof createMockTaskStateService>;

    beforeEach(() => {
      mockState = createMockTaskStateService({ loading: false, tasks: [] });

      TestBed.configureTestingModule({
        imports: [TaskListComponent],
        providers: [
          { provide: TaskStateService, useValue: mockState },
        ],
      });

      fixture = TestBed.createComponent(TaskListComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should display an empty-state message when the task list is empty', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="empty-state"]')).not.toBeNull();
    });

    it('should not display the task list when it is empty', () => {
      const el: HTMLElement = fixture.nativeElement;
      const list = el.querySelector('[data-testid="task-list"]');
      expect(list).toBeNull();
    });
  });

  describe('with mocked TaskStateService — tasks loaded', () => {
    let mockState: ReturnType<typeof createMockTaskStateService>;

    beforeEach(() => {
      mockState = createMockTaskStateService({
        loading: false,
        tasks: [TASK_PENDING, TASK_DONE],
      });

      TestBed.configureTestingModule({
        imports: [TaskListComponent],
        providers: [
          { provide: TaskStateService, useValue: mockState },
        ],
      });

      fixture = TestBed.createComponent(TaskListComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should not show the loading indicator when not loading', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="loading-indicator"]')).toBeNull();
    });

    it('should not show the empty-state message when tasks exist', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="empty-state"]')).toBeNull();
    });

    it('should render one task item per task', () => {
      const el: HTMLElement = fixture.nativeElement;
      const items = el.querySelectorAll('[data-testid="task-item"]');
      expect(items.length).toBe(2);
    });
  });

  describe('with mocked TaskStateService — filter controls', () => {
    let mockState: ReturnType<typeof createMockTaskStateService>;

    beforeEach(() => {
      mockState = createMockTaskStateService({
        loading: false,
        tasks: [TASK_PENDING],
        filter: 'all',
      });

      TestBed.configureTestingModule({
        imports: [TaskListComponent],
        providers: [
          { provide: TaskStateService, useValue: mockState },
        ],
      });

      fixture = TestBed.createComponent(TaskListComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should render filter controls for all, pending, and completed', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="filter-all"]')).not.toBeNull();
      expect(el.querySelector('[data-testid="filter-pending"]')).not.toBeNull();
      expect(el.querySelector('[data-testid="filter-completed"]')).not.toBeNull();
    });

    it('should update TaskStateService.filter to "pending" when the pending filter is clicked', () => {
      const el: HTMLElement = fixture.nativeElement;
      const pendingBtn = el.querySelector<HTMLButtonElement>('[data-testid="filter-pending"]');
      pendingBtn!.click();
      fixture.detectChanges();

      expect(mockState.filter()).toBe('pending');
    });

    it('should update TaskStateService.filter to "completed" when the completed filter is clicked', () => {
      const el: HTMLElement = fixture.nativeElement;
      const completedBtn = el.querySelector<HTMLButtonElement>('[data-testid="filter-completed"]');
      completedBtn!.click();
      fixture.detectChanges();

      expect(mockState.filter()).toBe('completed');
    });

    it('should update TaskStateService.filter to "all" when the all filter is clicked', () => {
      mockState.filter.set('pending');
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const allBtn = el.querySelector<HTMLButtonElement>('[data-testid="filter-all"]');
      allBtn!.click();
      fixture.detectChanges();

      expect(mockState.filter()).toBe('all');
    });
  });
});
