import { Component, OnInit, HostListener, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TaskStateService } from '../services/task-state.service';
import { TaskItemComponent } from '../task-item/task-item.component';
import { AuthStateService } from '../../auth/services/auth-state.service';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [CommonModule, FormsModule, TaskItemComponent, RouterLink],
  template: `
    <div class="task-list-container">
      <div class="task-list-header">
        <h2>My Tasks</h2>
        <a routerLink="/dashboard" data-testid="dashboard-link" class="btn-logout">
          Account
        </a>
        <button type="button" class="btn-logout" data-testid="logout-button" (click)="logout()">
          Logout
        </button>
      </div>

      <div class="create-task-trigger">
        <button
          type="button"
          class="btn-add-task"
          data-testid="open-create-modal-btn"
          (click)="openModal()"
        >
          + Add Task
        </button>
      </div>

      <!-- Create Task Modal -->
      <div
        *ngIf="showModal"
        class="modal-overlay"
        data-testid="create-task-modal-overlay"
        (click)="onOverlayClick($event)"
      >
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div class="modal-header">
            <h3 id="modal-title">New Task</h3>
            <button
              type="button"
              class="modal-close"
              aria-label="Close"
              data-testid="modal-close-btn"
              (click)="closeModal()"
            >&#x2715;</button>
          </div>
          <form class="modal-body" (ngSubmit)="submitCreate()">
            <div class="modal-field">
              <label for="modalTaskTitle">What needs to be done?</label>
              <input
                id="modalTaskTitle"
                data-testid="new-task-input"
                type="text"
                [(ngModel)]="newTaskTitle"
                name="newTaskTitle"
                placeholder="e.g. Buy groceries"
                autocomplete="off"
                autofocus
              />
            </div>
            <div class="modal-field">
              <label for="modalTaskDueDate">Due date <span class="field-optional">(optional)</span></label>
              <input
                id="modalTaskDueDate"
                data-testid="new-task-due-date-input"
                type="date"
                [(ngModel)]="newTaskDueDate"
                name="newTaskDueDate"
                aria-label="Due date for new task"
              />
            </div>
            <div class="modal-footer">
              <button type="button" class="btn-cancel" (click)="closeModal()">Cancel</button>
              <button
                type="submit"
                class="btn-primary"
                data-testid="create-task-btn"
                [disabled]="!newTaskTitle.trim()"
              >
                Save
              </button>
            </div>
          </form>
        </div>
      </div>

      <div class="filter-controls">
        <button
          data-testid="filter-all"
          [class.active]="taskState.filter() === 'all'"
          (click)="taskState.filter.set('all')"
        >
          All
        </button>
        <button
          data-testid="filter-pending"
          [class.active]="taskState.filter() === 'pending'"
          (click)="taskState.filter.set('pending')"
        >
          Pending
        </button>
        <button
          data-testid="filter-completed"
          [class.active]="taskState.filter() === 'completed'"
          (click)="taskState.filter.set('completed')"
        >
          Completed
        </button>
        <button
          data-testid="filter-overdue"
          [class.active]="taskState.filter() === 'overdue'"
          [attr.aria-pressed]="taskState.filter() === 'overdue'"
          (click)="taskState.filter.set('overdue')"
        >
          Overdue
          <span
            *ngIf="taskState.overdueCount() > 0"
            class="overdue-badge badge"
            aria-live="polite"
          >{{ taskState.overdueCount() }}</span>
        </button>
      </div>

      <div class="sort-controls">
        <button
          data-testid="sort-due-date"
          [class.active]="taskState.sortBy() === 'due_date'"
          [attr.aria-label]="'Sort by due date ' + taskState.sortDir()"
          (click)="toggleDueDateSort()"
        >
          Due Date
          <ng-container *ngIf="taskState.sortBy() === 'due_date'">
            {{ taskState.sortDir() === 'asc' ? '↑' : '↓' }}
          </ng-container>
        </button>
        <button
          *ngIf="taskState.sortBy() !== null"
          data-testid="clear-sort"
          (click)="clearSort()"
        >
          Clear Sort
        </button>
      </div>

      <div *ngIf="taskState.loading()" data-testid="loading-indicator" class="loading">
        Loading tasks...
      </div>

      <ng-container *ngIf="!taskState.loading()">
        <div
          *ngIf="taskState.tasks().length === 0 && taskState.filter() === 'overdue'"
          data-testid="overdue-empty-state"
          class="empty-state"
        >
          No overdue tasks. You are all caught up!
        </div>

        <div
          *ngIf="taskState.tasks().length === 0 && taskState.filter() !== 'overdue'"
          data-testid="empty-state"
          class="empty-state"
        >
          No tasks yet. Create your first task to get started.
        </div>

        <ul *ngIf="taskState.tasks().length > 0" data-testid="task-list" class="task-list">
          <li *ngFor="let task of taskState.tasks()">
            <app-task-item [task]="task" />
          </li>
        </ul>
      </ng-container>
    </div>
  `,
})
export class TaskListComponent implements OnInit {
  readonly taskState = inject(TaskStateService);
  private readonly authState = inject(AuthStateService);
  private readonly router = inject(Router);
  newTaskTitle = '';
  newTaskDueDate = '';
  showModal = false;

  ngOnInit(): void {
    this.taskState.loadTasks().subscribe();
  }

  openModal(): void {
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
    this.newTaskTitle = '';
    this.newTaskDueDate = '';
  }

  onOverlayClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-overlay')) {
      this.closeModal();
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.showModal) this.closeModal();
  }

  submitCreate(): void {
    const title = this.newTaskTitle.trim();
    if (!title) return;
    const dueDate = this.newTaskDueDate || null;
    this.taskState.createTask(title, dueDate).subscribe();
    this.closeModal();
  }

  toggleDueDateSort(): void {
    const currentSortBy = this.taskState.sortBy();
    if (currentSortBy === 'due_date') {
      // Toggle direction
      const newDir = this.taskState.sortDir() === 'asc' ? 'desc' : 'asc';
      this.taskState.sortDir.set(newDir);
    } else {
      // Activate sort by due_date with default ASC
      this.taskState.sortBy.set('due_date');
      this.taskState.sortDir.set('asc');
    }
    this.taskState.loadTasks().subscribe();
  }

  clearSort(): void {
    this.taskState.sortBy.set(null);
    this.taskState.loadTasks().subscribe();
  }

  logout(): void {
    this.authState.clearSession();
    this.router.navigate(['/login']);
  }
}
