import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import type { Task } from '../../shared/models/task.model';
import { TaskStateService } from '../services/task-state.service';

@Component({
  selector: 'app-task-item',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="group relative flex items-start gap-4 p-4 rounded-xl hover:bg-surface-container-low transition-colors duration-200" data-testid="task-item">
      <ng-container *ngIf="!editing">
        <!-- Circle toggle -->
        <button
          data-testid="toggle-completion"
          type="button"
          (click)="onToggle()"
          class="mt-1 w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all duration-200"
          [ngClass]="task.completed
            ? 'bg-primary border-primary'
            : 'border-primary/60 group-hover:border-primary group-hover:bg-primary/5'"
        >
          <span
            class="material-symbols-outlined text-[15px] transition-opacity"
            [ngClass]="task.completed ? 'text-on-primary opacity-100' : 'text-primary opacity-0 group-hover:opacity-60'"
            [ngStyle]="checkIconStyle"
          >check</span>
        </button>

        <!-- Title + metadata -->
        <div class="flex-1 min-w-0">
          <h3
            data-testid="task-title"
            class="text-on-surface font-semibold text-[15px] leading-snug"
            [ngClass]="task.completed ? 'line-through decoration-primary/60 decoration-2' : ''"
          >{{ task.title }}</h3>
        </div>

        <!-- Hover actions -->
        <div class="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity flex-shrink-0">
          <button
            data-testid="edit-button"
            type="button"
            (click)="startEditing()"
            class="p-1.5 text-on-surface-variant hover:text-primary transition-colors rounded-lg hover:bg-surface-container-high"
          >
            <span class="material-symbols-outlined text-[18px]">edit</span>
          </button>
          <button
            data-testid="delete-button"
            type="button"
            (click)="onDelete()"
            class="p-1.5 text-on-surface-variant hover:text-error transition-colors rounded-lg hover:bg-error-container/30"
          >
            <span class="material-symbols-outlined text-[18px]">delete</span>
          </button>
        </div>
      </ng-container>

      <ng-container *ngIf="editing">
        <form
          data-testid="edit-form"
          (submit)="onSubmitEdit($event)"
          class="flex items-center gap-2 w-full flex-wrap"
        >
          <input
            data-testid="edit-input"
            type="text"
            [value]="editTitle"
            (input)="onEditInput($event)"
            class="flex-1 px-4 py-2 bg-surface-container-low border-0 rounded-xl focus:ring-2 focus:ring-primary/20 focus:bg-surface-container-lowest transition-all outline-none text-on-surface min-w-0"
            autofocus
          />
          <button type="submit" class="px-4 py-2 bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-xl font-semibold text-sm shadow-sm transition-transform active:scale-95">Save</button>
          <button type="button" (click)="cancelEditing()" class="px-4 py-2 bg-surface-container-high text-on-surface-variant rounded-xl font-semibold text-sm transition-colors hover:bg-surface-container-highest">Cancel</button>
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

  get checkIconStyle(): Record<string, string> {
    return this.task.completed ? { 'font-variation-settings': "'FILL' 1" } : {};
  }

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
