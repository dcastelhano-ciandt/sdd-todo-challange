import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TaskStateService } from '../services/task-state.service';
import { TaskItemComponent } from '../task-item/task-item.component';
import { AuthStateService } from '../../auth/services/auth-state.service';
import { AuthApiService } from '../../auth/services/auth-api.service';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [CommonModule, FormsModule, TaskItemComponent, RouterLink],
  template: `
    <div class="bg-surface text-on-surface min-h-screen pb-24">
      <!-- Top Navigation -->
      <header class="w-full top-0 sticky z-40 bg-surface border-b border-outline-variant/20">
        <nav class="flex justify-between items-center h-16 px-8 max-w-[1440px] mx-auto">
          <div class="flex items-center gap-8">
            <span class="text-xl font-bold tracking-tighter text-primary">Task Flow</span>
            <div class="hidden md:flex items-center gap-6">
              <a class="text-primary font-semibold border-b-2 border-primary py-5 text-sm" href="#">Tasks</a>
              <a routerLink="/account" data-testid="dashboard-link" class="text-on-surface-variant hover:text-primary py-5 text-sm transition-colors">Account</a>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button type="button" class="p-2 hover:bg-surface-container-low rounded-full transition-colors">
              <span class="material-symbols-outlined text-on-surface-variant text-[22px]">notifications</span>
            </button>
            <button
              type="button"
              data-testid="logout-button"
              (click)="logout()"
              class="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center hover:ring-2 hover:ring-primary/30 transition-all"
              title="Sign out"
            >
              <span class="material-symbols-outlined text-on-surface-variant text-[20px]">logout</span>
            </button>
          </div>
        </nav>
      </header>

      <!-- Main content -->
      <main class="max-w-[720px] mx-auto px-6 py-12 md:py-16">
        <!-- Welcome header -->
        <header class="mb-10">
          <h1 class="text-4xl font-extrabold tracking-tight text-on-surface mb-2">{{ greeting }}, {{ username }}</h1>
          <p class="text-on-surface-variant font-medium opacity-80 text-sm">{{ todayLabel }}</p>
        </header>

        <!-- Search bar -->
        <div class="relative mb-8">
          <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <span class="material-symbols-outlined text-on-surface-variant opacity-60">search</span>
          </div>
          <input
            data-testid="search-input"
            type="text"
            [(ngModel)]="searchTerm"
            name="searchTerm"
            placeholder="Search through your Task Flow..."
            autocomplete="off"
            (input)="onSearchInput($any($event).target.value)"
            class="w-full bg-surface-container-low border-none rounded-xl py-4 pl-12 pr-12 focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all duration-200 placeholder:text-on-surface-variant/50 outline-none"
          />
          <div class="absolute inset-y-0 right-4 flex items-center">
            <span
              class="material-symbols-outlined text-on-surface-variant/40 cursor-pointer hover:text-on-surface"
              data-testid="clear-search"
              (click)="clearSearch()"
            >close</span>
          </div>
        </div>

        <!-- Filter tabs -->
        <div class="flex items-center gap-3 mb-10 overflow-x-auto hide-scrollbar">
          <button
            data-testid="filter-all"
            (click)="setFilter('all')"
            [ngClass]="taskState.filter() === 'all'
              ? 'bg-primary text-on-primary'
              : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-container-highest'"
            class="px-5 py-2 rounded-full text-sm font-semibold flex items-center gap-2 transition-all active:scale-95"
          >
            All
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold"
              [ngClass]="taskState.filter() === 'all' ? 'bg-on-primary/20' : 'bg-on-surface-variant/10'"
            >{{ allTasks.length }}</span>
          </button>
          <button
            data-testid="filter-pending"
            (click)="setFilter('pending')"
            [ngClass]="taskState.filter() === 'pending'
              ? 'bg-primary text-on-primary'
              : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-container-highest'"
            class="px-5 py-2 rounded-full text-sm font-semibold flex items-center gap-2 transition-all active:scale-95"
          >
            Pending
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold"
              [ngClass]="taskState.filter() === 'pending' ? 'bg-on-primary/20' : 'bg-on-surface-variant/10'"
            >{{ pendingCount }}</span>
          </button>
          <button
            data-testid="filter-completed"
            (click)="setFilter('completed')"
            [ngClass]="taskState.filter() === 'completed'
              ? 'bg-primary text-on-primary'
              : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-container-highest'"
            class="px-5 py-2 rounded-full text-sm font-semibold flex items-center gap-2 transition-all active:scale-95"
          >
            Completed
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold"
              [ngClass]="taskState.filter() === 'completed' ? 'bg-on-primary/20' : 'bg-on-surface-variant/10'"
            >{{ completedCount }}</span>
          </button>
        </div>

        <!-- New task input -->
        <form (ngSubmit)="submitCreate()" class="bg-surface-container-low rounded-xl p-2 mb-12 flex items-center gap-2 transition-all focus-within:bg-surface-container-lowest focus-within:shadow-sm">
          <div class="p-2 ml-1">
            <span class="material-symbols-outlined text-primary">add</span>
          </div>
          <input
            data-testid="new-task-input"
            type="text"
            [(ngModel)]="newTaskTitle"
            name="newTaskTitle"
            placeholder="What needs to be done?"
            autocomplete="off"
            class="flex-1 bg-transparent border-none focus:ring-0 py-3 text-on-surface placeholder:text-on-surface-variant/40 outline-none"
          />
          <button
            type="submit"
            data-testid="create-task-btn"
            [disabled]="!newTaskTitle.trim()"
            class="bg-gradient-to-br from-primary to-primary-container text-on-primary px-6 py-2.5 rounded-xl font-bold text-sm shadow-sm transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add Task
          </button>
        </form>

        <!-- Loading -->
        <div *ngIf="taskState.loading()" data-testid="loading-indicator" class="py-16 text-center text-on-surface-variant text-sm">
          Loading tasks...
        </div>

        <ng-container *ngIf="!taskState.loading()">
          <!-- Empty state (no tasks at all) -->
          <div *ngIf="allTasks.length === 0" data-testid="empty-state" class="py-16 text-center text-on-surface-variant">
            <span class="material-symbols-outlined text-[48px] opacity-30 block mb-4">checklist</span>
            <ng-container *ngIf="searchTerm; else defaultEmpty">
              No results for '{{ searchTerm }}'
            </ng-container>
            <ng-template #defaultEmpty>
              No tasks yet. Create your first task to get started.
            </ng-template>
          </div>

          <ng-container *ngIf="allTasks.length > 0">
            <!-- Pending tasks -->
            <section *ngIf="pendingTasks.length > 0" data-testid="task-list" class="space-y-1 mb-4">
              <app-task-item *ngFor="let task of pendingTasks" [task]="task" />
            </section>

            <!-- Completed section (collapsible) -->
            <section *ngIf="completedTasks.length > 0" class="mt-10">
              <button
                type="button"
                (click)="completedExpanded = !completedExpanded"
                class="flex items-center gap-2 text-on-surface-variant hover:text-on-surface transition-colors font-semibold py-4 mb-2 group"
              >
                <span class="material-symbols-outlined transition-transform duration-200"
                  [ngClass]="completedExpanded ? 'rotate-0' : '-rotate-90'"
                >expand_more</span>
                <span>Completed ({{ completedTasks.length }})</span>
              </button>
              <div *ngIf="completedExpanded" class="space-y-1 opacity-60">
                <app-task-item *ngFor="let task of completedTasks" [task]="task" />
              </div>
            </section>
          </ng-container>
        </ng-container>
      </main>
    </div>
  `,
})
export class TaskListComponent implements OnInit, OnDestroy {
  readonly taskState = inject(TaskStateService);
  private readonly authState = inject(AuthStateService);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);
  newTaskTitle = '';
  searchTerm = '';
  completedExpanded = true;
  username = '';
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  get greeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }

  get allTasks() {
    return this.taskState.tasks();
  }

  get pendingTasks() {
    return this.taskState.tasks().filter(t => !t.completed);
  }

  get completedTasks() {
    return this.taskState.tasks().filter(t => t.completed);
  }

  get pendingCount(): number {
    return this.pendingTasks.length;
  }

  get completedCount(): number {
    return this.completedTasks.length;
  }

  get todayLabel(): string {
    return new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  }

  ngOnInit(): void {
    this.taskState.loadTasks().subscribe();
    this.authApi.getProfile().subscribe({
      next: (profile) => {
        const local = profile.email.split('@')[0];
        this.username = local.charAt(0).toUpperCase() + local.slice(1);
      },
    });
  }

  ngOnDestroy(): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
  }

  onSearchInput(value: string): void {
    this.searchTerm = value;
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.taskState.loadTasks(this.searchTerm || undefined).subscribe();
    }, 300);
  }

  clearSearch(): void {
    this.searchTerm = '';
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    this.taskState.loadTasks().subscribe();
  }

  setFilter(value: 'all' | 'pending' | 'completed'): void {
    this.taskState.filter.set(value);
    this.taskState.loadTasks(this.searchTerm || undefined).subscribe();
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
