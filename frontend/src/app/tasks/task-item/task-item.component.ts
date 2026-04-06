import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import type { Task } from '../../shared/models/task.model';
import { TaskStateService } from '../services/task-state.service';

@Component({
  selector: 'app-task-item',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styles: [`
    .task-title.completed {
      text-decoration: line-through;
      color: #888;
    }
  `],
  template: `
    <div class="task-item" data-testid="task-item">
      <ng-container *ngIf="!editing">
        <span
          data-testid="task-title"
          class="task-title"
          [class.completed]="task.completed"
        >{{ task.title }}</span>

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

  onToggle(): void {
    this.taskState.toggleCompletion(this.task.id).subscribe();
  }

  startEditing(): void {
    this.editTitle = this.task.title;
    this.editing = true;
  }

  cancelEditing(): void {
    this.editing = false;
  }

  onEditInput(event: Event): void {
    this.editTitle = (event.target as HTMLInputElement).value;
  }

  onSubmitEdit(event: Event): void {
    event.preventDefault();
    const trimmed = this.editTitle.trim();
    if (!trimmed) {
      return;
    }
    this.taskState.updateTask(this.task.id, trimmed).subscribe({
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
