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
    filter: signal<'all' | 'pending' | 'completed'>('all'),
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

      expect(mockState.updateTask).toHaveBeenCalledWith(TASK_PENDING.id, 'Updated title');
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
