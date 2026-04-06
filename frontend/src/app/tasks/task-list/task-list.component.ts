import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TaskStateService } from '../services/task-state.service';
import { TaskItemComponent } from '../task-item/task-item.component';
import { AuthStateService } from '../../auth/services/auth-state.service';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [CommonModule, FormsModule, TaskItemComponent],
  template: `
    <div class="task-list-container">
      <div class="task-list-header">
        <h2>My Tasks</h2>
        <button type="button" class="btn-logout" data-testid="logout-button" (click)="logout()">
          Logout
        </button>
      </div>

      <form class="create-task-form" (ngSubmit)="submitCreate()">
        <div class="create-task-field">
          <input
            data-testid="new-task-input"
            type="text"
            [(ngModel)]="newTaskTitle"
            name="newTaskTitle"
            placeholder="What needs to be done?"
            autocomplete="off"
          />
          <button type="submit" data-testid="create-task-btn" [disabled]="!newTaskTitle.trim()">
            Add Task
          </button>
        </div>
      </form>

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
      </div>

      <div *ngIf="taskState.loading()" data-testid="loading-indicator" class="loading">
        Loading tasks...
      </div>

      <ng-container *ngIf="!taskState.loading()">
        <div
          *ngIf="taskState.tasks().length === 0"
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

  ngOnInit(): void {
    this.taskState.loadTasks().subscribe();
  }

  submitCreate(): void {
    const title = this.newTaskTitle.trim();
    if (!title) return;
    this.taskState.createTask(title).subscribe();
    this.newTaskTitle = '';
  }

  logout(): void {
    this.authState.clearSession();
    this.router.navigate(['/login']);
  }
}
