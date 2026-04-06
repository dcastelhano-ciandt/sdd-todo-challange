import { Component, Input, inject } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import type { Task } from '../../shared/models/task.model';
import { TaskStateService, isOverdue } from '../services/task-state.service';

@Component({
  selector: 'app-task-item',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePipe],
  styles: [`
    .task-title.completed {
      text-decoration: line-through;
      color: #888;
    }
    .due-date-label {
      font-size: 0.85em;
      color: #555;
      margin-left: 0.5em;
    }
    .overdue-indicator {
      color: #c0392b;
      font-weight: bold;
      text-decoration: underline;
      margin-left: 0.5em;
    }
    .task--overdue .task-title {
      color: #c0392b;
    }
  `],
  template: `
    <div class="task-item"
         [class.task--overdue]="taskIsOverdue"
         data-testid="task-item">
      <ng-container *ngIf="!editing">
        <span
          data-testid="task-title"
          class="task-title"
          [class.completed]="task.completed"
        >{{ task.title }}</span>

        <span
          *ngIf="task.due_date"
          class="due-date-label"
          [attr.aria-label]="'Due: ' + (task.due_date | date:'MMM d, y')"
        >{{ task.due_date | date:'MMM d, y' }}</span>

        <span
          *ngIf="taskIsOverdue"
          class="overdue-indicator"
          aria-label="Overdue"
          role="img"
        >&#9888; Overdue</span>

        <button
          data-testid="toggle-completion"
          (click)="onToggle()"
          type="button"
        >
          {{ task.completed ? 'Reopen' : 'Complete' }}
        </button>

        <button
          data-testid="edit-button"
          (click)="startEditing()"
          type="button"
        >
          Edit
        </button>

        <button
          data-testid="delete-button"
          (click)="onDelete()"
          type="button"
        >
          Delete
        </button>
      </ng-container>

      <ng-container *ngIf="editing">
        <form
          data-testid="edit-form"
          (submit)="onSubmitEdit($event)"
        >
          <input
            data-testid="edit-input"
            type="text"
            [value]="editTitle"
            (input)="onEditInput($event)"
          />
          <input
            type="date"
            [value]="editDueDate"
            name="editDueDate"
            aria-label="Due date"
            (input)="onEditDueDateInput($event)"
          />
          <button type="submit">Save</button>
          <button type="button" (click)="cancelEditing()">Cancel</button>
        </form>
      </ng-container>
    </div>
  `,
})
export class TaskItemComponent {
  @Input() task!: Task;

  private readonly taskState = inject(TaskStateService);

  editing = false;
  editTitle = '';
  editDueDate = '';

  get taskIsOverdue(): boolean {
    return isOverdue(this.task);
  }

  onToggle(): void {
    this.taskState.toggleCompletion(this.task.id).subscribe();
  }

  startEditing(): void {
    this.editTitle = this.task.title;
    this.editDueDate = this.task.due_date ?? '';
    this.editing = true;
  }

  cancelEditing(): void {
    this.editing = false;
  }

  onEditInput(event: Event): void {
    this.editTitle = (event.target as HTMLInputElement).value;
  }

  onEditDueDateInput(event: Event): void {
    this.editDueDate = (event.target as HTMLInputElement).value;
  }

  onSubmitEdit(event: Event): void {
    event.preventDefault();
    const trimmed = this.editTitle.trim();
    if (!trimmed) {
      return;
    }
    const dueDate: string | null = this.editDueDate.trim() || null;
    this.taskState.updateTask(this.task.id, trimmed, dueDate).subscribe({
      next: () => {
        this.editing = false;
      },
    });
  }

  onDelete(): void {
    if (!confirm(`Delete "${this.task.title}"?`)) return;
    this.taskState.deleteTask(this.task.id).subscribe();
  }
}
