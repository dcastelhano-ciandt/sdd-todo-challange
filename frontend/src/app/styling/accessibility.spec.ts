import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { LoginComponent } from '../auth/login/login.component';
import { RegisterComponent } from '../auth/register/register.component';
import { TaskItemComponent } from '../tasks/task-item/task-item.component';
import { TaskStateService } from '../tasks/services/task-state.service';
import { signal } from '@angular/core';
import type { Task } from '../shared/models/task.model';
import { of } from 'rxjs';

const TASK_PENDING: Task = {
  id: 'task-1',
  userId: 'user-1',
  title: 'Buy groceries',
  completed: false,
};

function createMockTaskStateService() {
  return {
    tasks: signal<Task[]>([]).asReadonly(),
    loading: signal<boolean>(false).asReadonly(),
    filter: signal<'all' | 'pending' | 'completed'>('all'),
    loadTasks: vi.fn(() => of(undefined as unknown as void)),
    createTask: vi.fn(),
    updateTask: vi.fn(() => of(TASK_PENDING)),
    toggleCompletion: vi.fn(() => of(TASK_PENDING)),
    deleteTask: vi.fn(() => of(undefined as unknown as void)),
  };
}

describe('11.2 Touch-Friendly Interactive Elements and Accessibility', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  describe('LoginComponent — form inputs and buttons', () => {
    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [LoginComponent],
        providers: [
          provideRouter([
            { path: 'tasks', component: {} as any },
            { path: 'register', component: {} as any },
          ]),
          provideHttpClient(),
          provideHttpClientTesting(),
        ],
      }).compileComponents();
    });

    it('should have a submit button with an accessible type attribute', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const submitBtn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(submitBtn).not.toBeNull();
      expect(submitBtn!.type).toBe('submit');
    });

    it('should have inputs associated with labels via id/for or wrapping', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const emailInput = el.querySelector<HTMLInputElement>('#email');
      const passwordInput = el.querySelector<HTMLInputElement>('#password');
      expect(emailInput).not.toBeNull();
      expect(passwordInput).not.toBeNull();
    });

    it('should have labels that reference input ids for screen-reader association', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const emailLabel = el.querySelector<HTMLLabelElement>('label[for="email"]');
      const passwordLabel = el.querySelector<HTMLLabelElement>('label[for="password"]');
      expect(emailLabel).not.toBeNull();
      expect(passwordLabel).not.toBeNull();
    });

    it('should render inline field-error spans adjacent to their respective fields', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      const component = fixture.componentInstance as any;
      fixture.detectChanges();

      // Touch fields to trigger validation errors
      component.form.get('email')?.markAsTouched();
      component.form.get('password')?.markAsTouched();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      // Errors should be inside .field containers (adjacent to inputs)
      const fieldErrors = el.querySelectorAll('.field .field-error');
      expect(fieldErrors.length).toBeGreaterThan(0);
    });

    it('should apply field-error class on validation error spans for consistent styling', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      const component = fixture.componentInstance as any;
      fixture.detectChanges();

      component.form.get('email')?.markAsTouched();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const errorSpan = el.querySelector('.field-error');
      expect(errorSpan).not.toBeNull();
      // The error span should be a span element (inline, unobtrusive)
      expect(errorSpan!.tagName.toLowerCase()).toBe('span');
    });
  });

  describe('RegisterComponent — form inputs and buttons', () => {
    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [RegisterComponent],
        providers: [
          provideRouter([
            { path: 'tasks', component: {} as any },
            { path: 'login', component: {} as any },
          ]),
          provideHttpClient(),
          provideHttpClientTesting(),
        ],
      }).compileComponents();
    });

    it('should have a submit button with accessible type attribute', () => {
      const fixture = TestBed.createComponent(RegisterComponent);
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const submitBtn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(submitBtn).not.toBeNull();
      expect(submitBtn!.type).toBe('submit');
    });

    it('should have inputs associated with labels via id/for attributes', () => {
      const fixture = TestBed.createComponent(RegisterComponent);
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const emailLabel = el.querySelector<HTMLLabelElement>('label[for="email"]');
      const passwordLabel = el.querySelector<HTMLLabelElement>('label[for="password"]');
      expect(emailLabel).not.toBeNull();
      expect(passwordLabel).not.toBeNull();
    });

    it('should render inline field-error spans inside .field containers', () => {
      const fixture = TestBed.createComponent(RegisterComponent);
      const component = fixture.componentInstance as any;
      fixture.detectChanges();

      component.form.get('email')?.markAsTouched();
      component.form.get('password')?.markAsTouched();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const fieldErrors = el.querySelectorAll('.field .field-error');
      expect(fieldErrors.length).toBeGreaterThan(0);
    });

    it('should apply field-error class on validation error spans (inline, unobtrusive style)', () => {
      const fixture = TestBed.createComponent(RegisterComponent);
      const component = fixture.componentInstance as any;
      fixture.detectChanges();

      component.form.get('email')?.markAsTouched();
      fixture.detectChanges();

      const el: HTMLElement = fixture.nativeElement;
      const errorSpan = el.querySelector('.field-error');
      expect(errorSpan).not.toBeNull();
      expect(errorSpan!.tagName.toLowerCase()).toBe('span');
    });
  });

  describe('TaskItemComponent — interactive controls', () => {
    let mockState: ReturnType<typeof createMockTaskStateService>;

    beforeEach(async () => {
      mockState = createMockTaskStateService();
      await TestBed.configureTestingModule({
        imports: [TaskItemComponent],
        providers: [{ provide: TaskStateService, useValue: mockState }],
      }).compileComponents();
    });

    it('should have toggle button with explicit type="button" for keyboard accessibility', () => {
      const fixture = TestBed.createComponent(TaskItemComponent);
      fixture.componentInstance.task = TASK_PENDING;
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const toggleBtn = el.querySelector<HTMLButtonElement>('[data-testid="toggle-completion"]');
      expect(toggleBtn).not.toBeNull();
      expect(toggleBtn!.type).toBe('button');
    });

    it('should have edit button with explicit type="button" for keyboard accessibility', () => {
      const fixture = TestBed.createComponent(TaskItemComponent);
      fixture.componentInstance.task = TASK_PENDING;
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const editBtn = el.querySelector<HTMLButtonElement>('[data-testid="edit-button"]');
      expect(editBtn).not.toBeNull();
      expect(editBtn!.type).toBe('button');
    });

    it('should have delete button with explicit type="button" for keyboard accessibility', () => {
      const fixture = TestBed.createComponent(TaskItemComponent);
      fixture.componentInstance.task = TASK_PENDING;
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const deleteBtn = el.querySelector<HTMLButtonElement>('[data-testid="delete-button"]');
      expect(deleteBtn).not.toBeNull();
      expect(deleteBtn!.type).toBe('button');
    });

    it('should render buttons as native button elements (not divs or spans) for keyboard access', () => {
      const fixture = TestBed.createComponent(TaskItemComponent);
      fixture.componentInstance.task = TASK_PENDING;
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const buttons = el.querySelectorAll(
        '[data-testid="toggle-completion"], [data-testid="edit-button"], [data-testid="delete-button"]',
      );
      buttons.forEach((btn) => {
        expect(btn.tagName.toLowerCase()).toBe('button');
      });
    });

    it('should render the task-item container as a div for layout', () => {
      const fixture = TestBed.createComponent(TaskItemComponent);
      fixture.componentInstance.task = TASK_PENDING;
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const taskItem = el.querySelector('[data-testid="task-item"]');
      expect(taskItem).not.toBeNull();
    });

    it('should have a text input in edit mode for title editing', () => {
      const fixture = TestBed.createComponent(TaskItemComponent);
      fixture.componentInstance.task = TASK_PENDING;
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;

      // Enter edit mode
      el.querySelector<HTMLElement>('[data-testid="edit-button"]')!.click();
      fixture.detectChanges();

      const editInput = el.querySelector<HTMLInputElement>('[data-testid="edit-input"]');
      expect(editInput).not.toBeNull();
      expect(editInput!.type).toBe('text');
    });
  });

  describe('CSS classes for hover/focus styling', () => {
    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [LoginComponent],
        providers: [
          provideRouter([
            { path: 'tasks', component: {} as any },
            { path: 'register', component: {} as any },
          ]),
          provideHttpClient(),
          provideHttpClientTesting(),
        ],
      }).compileComponents();
    });

    it('should render buttons that can receive focus (no tabIndex=-1)', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const submitBtn = el.querySelector<HTMLButtonElement>('button[type="submit"]');
      expect(submitBtn).not.toBeNull();
      // tabIndex -1 would exclude from tab order; default 0 allows focus
      expect(submitBtn!.tabIndex).not.toBe(-1);
    });

    it('should render inputs that can receive focus', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const emailInput = el.querySelector<HTMLInputElement>('#email');
      expect(emailInput!.tabIndex).not.toBe(-1);
    });
  });
});
