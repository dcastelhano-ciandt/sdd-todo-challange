import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { TaskItemComponent } from './task-item.component';
import { TaskStateService } from '../services/task-state.service';
import { signal } from '@angular/core';
import type { Task } from '../../shared/models/task.model';
import { Observable, of, throwError } from 'rxjs';

const TASK_PENDING: Task = {
  id: 'task-1',
  userId: 'user-1',
  title: 'Buy groceries',
  completed: false,
};

const TASK_DONE: Task = {
  id: 'task-2',
  userId: 'user-1',
  title: 'Clean house',
  completed: true,
};

function createMockTaskStateService() {
  return {
    tasks: signal<Task[]>([]).asReadonly(),
    loading: signal<boolean>(false).asReadonly(),
    filter: signal<'all' | 'pending' | 'completed' | 'overdue'>('all'),
    sortBy: signal<'due_date' | null>(null),
    sortDir: signal<'asc' | 'desc'>('asc'),
    overdueCount: signal<number>(0).asReadonly(),
    loadTasks: vi.fn(() => of(undefined as unknown as void)),
    createTask: vi.fn((title: string, dueDate?: string | null) => of({ ...TASK_PENDING, title })),
    updateTask: vi.fn((taskId: string, title: string, dueDate?: string | null) =>
      of({ ...TASK_PENDING, title }),
    ),
    toggleCompletion: vi.fn((taskId: string) =>
      of({ ...TASK_PENDING, completed: !TASK_PENDING.completed }),
    ),
    deleteTask: vi.fn((taskId: string) => of(undefined as unknown as void)),
  };
}

describe('TaskItemComponent', () => {
  let fixture: ReturnType<typeof TestBed.createComponent<TaskItemComponent>>;
  let component: TaskItemComponent;
  let mockState: ReturnType<typeof createMockTaskStateService>;

  function setup(task: Task) {
    mockState = createMockTaskStateService();

    TestBed.configureTestingModule({
      imports: [TaskItemComponent],
      providers: [{ provide: TaskStateService, useValue: mockState }],
    });

    fixture = TestBed.createComponent(TaskItemComponent);
    component = fixture.componentInstance;
    component.task = task;
    fixture.detectChanges();
  }

  describe('pending task display', () => {
    beforeEach(() => setup(TASK_PENDING));

    it('should display the task title', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.textContent).toContain(TASK_PENDING.title);
    });

    it('should not apply a completed visual class to a pending task', () => {
      const el: HTMLElement = fixture.nativeElement;
      const titleEl = el.querySelector('[data-testid="task-title"]');
      expect(titleEl?.classList.contains('completed')).toBe(false);
    });
  });

  describe('completed task display', () => {
    beforeEach(() => setup(TASK_DONE));

    it('should display the task title', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.textContent).toContain(TASK_DONE.title);
    });

    it('should apply a completed visual class to a completed task title', () => {
      const el: HTMLElement = fixture.nativeElement;
      const titleEl = el.querySelector('[data-testid="task-title"]');
      expect(titleEl?.classList.contains('completed')).toBe(true);
    });
  });

  describe('completion toggle', () => {
    beforeEach(() => setup(TASK_PENDING));

    it('should render a toggle control', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="toggle-completion"]')).not.toBeNull();
    });

    it('should call TaskStateService.toggleCompletion with the task id when toggle is clicked', () => {
      const el: HTMLElement = fixture.nativeElement;
      const toggle = el.querySelector<HTMLElement>('[data-testid="toggle-completion"]');
      toggle!.click();
      fixture.detectChanges();

      expect(mockState.toggleCompletion).toHaveBeenCalledWith(TASK_PENDING.id);
    });
  });

  describe('inline edit', () => {
    beforeEach(() => setup(TASK_PENDING));

    it('should render an edit control', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="edit-button"]')).not.toBeNull();
    });

    it('should show an edit form when the edit control is clicked', () => {
      const el: HTMLElement = fixture.nativeElement;
      const editBtn = el.querySelector<HTMLElement>('[data-testid="edit-button"]');
      editBtn!.click();
      fixture.detectChanges();

      expect(el.querySelector('[data-testid="edit-form"]')).not.toBeNull();
    });

    it('should pre-populate the edit input with the current title', () => {
      const el: HTMLElement = fixture.nativeElement;
      el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
      fixture.detectChanges();

      const input = el.querySelector<HTMLInputElement>('[data-testid="edit-input"]');
      expect(input?.value).toBe(TASK_PENDING.title);
    });

    it('should call TaskStateService.updateTask with the task id and new title on submit', () => {
      const el: HTMLElement = fixture.nativeElement;
      el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
      fixture.detectChanges();

      const input = el.querySelector<HTMLInputElement>('[data-testid="edit-input"]');
      input!.value = 'Updated title';
      input!.dispatchEvent(new Event('input'));
      fixture.detectChanges();

      const form = el.querySelector<HTMLFormElement>('[data-testid="edit-form"]');
      form!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();

      // Now called with (taskId, title, dueDate) — dueDate is null when no date was set
      expect(mockState.updateTask).toHaveBeenCalledWith(TASK_PENDING.id, 'Updated title', null);
    });

    it('should not call updateTask when the title is empty on submit', () => {
      const el: HTMLElement = fixture.nativeElement;
      el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
      fixture.detectChanges();

      const input = el.querySelector<HTMLInputElement>('[data-testid="edit-input"]');
      input!.value = '';
      input!.dispatchEvent(new Event('input'));
      fixture.detectChanges();

      const form = el.querySelector<HTMLFormElement>('[data-testid="edit-form"]');
      form!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();

      expect(mockState.updateTask).not.toHaveBeenCalled();
    });

    it('should exit edit mode after a successful update', () => {
      const el: HTMLElement = fixture.nativeElement;
      el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
      fixture.detectChanges();

      const input = el.querySelector<HTMLInputElement>('[data-testid="edit-input"]');
      input!.value = 'New title';
      input!.dispatchEvent(new Event('input'));
      fixture.detectChanges();

      const form = el.querySelector<HTMLFormElement>('[data-testid="edit-form"]');
      form!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();

      expect(el.querySelector('[data-testid="edit-form"]')).toBeNull();
    });
  });

  describe('delete', () => {
    beforeEach(() => setup(TASK_PENDING));

    it('should render a delete control', () => {
      const el: HTMLElement = fixture.nativeElement;
      expect(el.querySelector('[data-testid="delete-button"]')).not.toBeNull();
    });

    it('should call TaskStateService.deleteTask with the task id when delete is clicked', () => {
      const el: HTMLElement = fixture.nativeElement;
      const deleteBtn = el.querySelector<HTMLElement>('[data-testid="delete-button"]');
      deleteBtn!.click();
      fixture.detectChanges();

      expect(mockState.deleteTask).toHaveBeenCalledWith(TASK_PENDING.id);
    });
  });
});

// ---------------------------------------------------------------------------
// Due Dates + Overdue — TaskItemComponent extensions (tasks 9.1, 9.2)
// ---------------------------------------------------------------------------

/** Returns a date string N days from today (negative = past). */
function daysFromToday(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

const TASK_WITH_DATE: Task = {
  id: 'task-with-date',
  userId: 'user-1',
  title: 'Task with due date',
  completed: false,
  due_date: '2026-08-15',
};

const TASK_OVERDUE: Task = {
  id: 'task-overdue',
  userId: 'user-1',
  title: 'Overdue task',
  completed: false,
  due_date: daysFromToday(-1),
};

const TASK_COMPLETED_OVERDUE: Task = {
  id: 'task-completed-overdue',
  userId: 'user-1',
  title: 'Done overdue',
  completed: true,
  due_date: daysFromToday(-1),
};

function createMockStateForItem() {
  return {
    tasks: signal<Task[]>([]).asReadonly(),
    loading: signal<boolean>(false).asReadonly(),
    filter: signal<'all' | 'pending' | 'completed' | 'overdue'>('all'),
    sortBy: signal<'due_date' | null>(null),
    sortDir: signal<'asc' | 'desc'>('asc'),
    overdueCount: signal<number>(0).asReadonly(),
    loadTasks: vi.fn(() => of(undefined as unknown as void)),
    createTask: vi.fn((title: string) => of({ ...TASK_PENDING, title })),
    updateTask: vi.fn((taskId: string, title: string) =>
      of({ ...TASK_PENDING, title }),
    ),
    toggleCompletion: vi.fn((taskId: string) =>
      of({ ...TASK_PENDING, completed: !TASK_PENDING.completed }),
    ),
    deleteTask: vi.fn((taskId: string) => of(undefined as unknown as void)),
  };
}

describe('TaskItemComponent — due date display (task 9.1)', () => {
  let fixture: ReturnType<typeof TestBed.createComponent<TaskItemComponent>>;
  let mockState: ReturnType<typeof createMockStateForItem>;

  function setup(task: Task) {
    mockState = createMockStateForItem();

    TestBed.configureTestingModule({
      imports: [TaskItemComponent],
      providers: [{ provide: TaskStateService, useValue: mockState }],
    });

    fixture = TestBed.createComponent(TaskItemComponent);
    fixture.componentInstance.task = task;
    fixture.detectChanges();
  }

  describe('task with due_date', () => {
    beforeEach(() => setup(TASK_WITH_DATE));

    it('should render the due date label when due_date is set', () => {
      const el: HTMLElement = fixture.nativeElement;
      const label = el.querySelector('.due-date-label');
      expect(label).not.toBeNull();
    });

    it('should include "Due:" in the due date label aria-label', () => {
      const el: HTMLElement = fixture.nativeElement;
      const label = el.querySelector('.due-date-label');
      expect(label?.getAttribute('aria-label')).toMatch(/Due:/);
    });
  });

  describe('task without due_date', () => {
    beforeEach(() => setup({ ...TASK_PENDING, due_date: null }));

    it('should NOT render the due date label when due_date is absent', () => {
      const el: HTMLElement = fixture.nativeElement;
      const label = el.querySelector('.due-date-label');
      expect(label).toBeNull();
    });
  });

  describe('overdue task', () => {
    beforeEach(() => setup(TASK_OVERDUE));

    it('should render the overdue indicator for a past-due incomplete task', () => {
      const el: HTMLElement = fixture.nativeElement;
      const indicator = el.querySelector('.overdue-indicator');
      expect(indicator).not.toBeNull();
    });

    it('should have aria-label="Overdue" on the overdue indicator', () => {
      const el: HTMLElement = fixture.nativeElement;
      const indicator = el.querySelector('.overdue-indicator');
      expect(indicator?.getAttribute('aria-label')).toBe('Overdue');
    });

    it('should have role="img" on the overdue indicator', () => {
      const el: HTMLElement = fixture.nativeElement;
      const indicator = el.querySelector('.overdue-indicator');
      expect(indicator?.getAttribute('role')).toBe('img');
    });

    it('should apply task--overdue class to the task item', () => {
      const el: HTMLElement = fixture.nativeElement;
      const taskItem = el.querySelector('.task-item');
      expect(taskItem?.classList.contains('task--overdue')).toBe(true);
    });
  });

  describe('completed overdue task', () => {
    beforeEach(() => setup(TASK_COMPLETED_OVERDUE));

    it('should NOT render the overdue indicator for a completed task', () => {
      const el: HTMLElement = fixture.nativeElement;
      const indicator = el.querySelector('.overdue-indicator');
      expect(indicator).toBeNull();
    });

    it('should NOT apply task--overdue class to a completed task', () => {
      const el: HTMLElement = fixture.nativeElement;
      const taskItem = el.querySelector('.task-item');
      expect(taskItem?.classList.contains('task--overdue')).toBe(false);
    });
  });
});

describe('TaskItemComponent — due date edit (task 9.2)', () => {
  let fixture: ReturnType<typeof TestBed.createComponent<TaskItemComponent>>;
  let component: TaskItemComponent;
  let mockState: ReturnType<typeof createMockStateForItem>;

  function setup(task: Task) {
    mockState = createMockStateForItem();

    TestBed.configureTestingModule({
      imports: [TaskItemComponent],
      providers: [{ provide: TaskStateService, useValue: mockState }],
    });

    fixture = TestBed.createComponent(TaskItemComponent);
    component = fixture.componentInstance;
    component.task = task;
    fixture.detectChanges();
  }

  beforeEach(() => setup(TASK_WITH_DATE));

  it('should render a date input in edit mode', () => {
    const el: HTMLElement = fixture.nativeElement;
    el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
    fixture.detectChanges();

    const dateInput = el.querySelector<HTMLInputElement>('input[type="date"]');
    expect(dateInput).not.toBeNull();
  });

  it('should have aria-label="Due date" on the date input', () => {
    const el: HTMLElement = fixture.nativeElement;
    el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
    fixture.detectChanges();

    const dateInput = el.querySelector<HTMLInputElement>('input[type="date"]');
    expect(dateInput?.getAttribute('aria-label')).toBe('Due date');
  });

  it('should pre-populate the date input with the current due_date', () => {
    const el: HTMLElement = fixture.nativeElement;
    el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
    fixture.detectChanges();

    const dateInput = el.querySelector<HTMLInputElement>('input[type="date"]');
    expect(dateInput?.value).toBe(TASK_WITH_DATE.due_date);
  });

  it('should call updateTask with the new due date on submit', () => {
    const el: HTMLElement = fixture.nativeElement;
    el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
    fixture.detectChanges();

    const titleInput = el.querySelector<HTMLInputElement>('[data-testid="edit-input"]');
    titleInput!.value = 'Updated title';
    titleInput!.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const dateInput = el.querySelector<HTMLInputElement>('input[type="date"]');
    dateInput!.value = '2026-12-01';
    dateInput!.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const form = el.querySelector<HTMLFormElement>('[data-testid="edit-form"]');
    form!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();

    expect(mockState.updateTask).toHaveBeenCalledWith(
      TASK_WITH_DATE.id,
      'Updated title',
      '2026-12-01',
    );
  });
});
