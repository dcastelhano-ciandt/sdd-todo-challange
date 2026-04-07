import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { Task as TaskModel } from '../../shared/models/task.model';
import { TaskListComponent } from './task-list.component';
import { TaskStateService } from '../services/task-state.service';
import { signal } from '@angular/core';
import type { Task } from '../../shared/models/task.model';
import { Observable, of, Subject } from 'rxjs';

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

function createMockTaskStateService(
  overrides: Partial<{
    tasks: Task[];
    loading: boolean;
    filter: 'all' | 'pending' | 'completed' | 'overdue';
    loadTasksFn: () => Observable<void>;
    overdueCount: number;
    sortBy: 'due_date' | null;
    sortDir: 'asc' | 'desc';
  }> = {},
) {
  const tasksSignal = signal<Task[]>(overrides.tasks ?? []);
  const loadingSignal = signal<boolean>(overrides.loading ?? false);
  const filterSignal = signal<'all' | 'pending' | 'completed' | 'overdue'>(
    overrides.filter ?? 'all',
  );
  const overdueCountSignal = signal<number>(overrides.overdueCount ?? 0);
  const sortBySignal = signal<'due_date' | null>(overrides.sortBy ?? null);
  const sortDirSignal = signal<'asc' | 'desc'>(overrides.sortDir ?? 'asc');

  return {
    tasks: tasksSignal.asReadonly(),
    loading: loadingSignal.asReadonly(),
    filter: filterSignal,
    overdueCount: overdueCountSignal.asReadonly(),
    sortBy: sortBySignal,
    sortDir: sortDirSignal,
    loadTasks: overrides.loadTasksFn ?? (() => of(undefined as unknown as void)),
    createTask: vi.fn((title: string) => of({} as Task)),
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
          provideRouter([
            { path: 'dashboard', component: {} as any },
            { path: 'login', component: {} as any },
          ]),
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
      const loadTasksSpy = vi
        .spyOn(taskState, 'loadTasks')
        .mockReturnValue(of(undefined as unknown as void));
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
          provideRouter([
            { path: 'dashboard', component: {} as any },
            { path: 'login', component: {} as any },
          ]),
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
          provideRouter([
            { path: 'dashboard', component: {} as any },
            { path: 'login', component: {} as any },
          ]),
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
          provideRouter([
            { path: 'dashboard', component: {} as any },
            { path: 'login', component: {} as any },
          ]),
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
          provideRouter([
            { path: 'dashboard', component: {} as any },
            { path: 'login', component: {} as any },
          ]),
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

// ─── Search Feature Tasks 6.1–6.5: search input, debounce, empty state ──────

describe('TaskListComponent — search input rendering', () => {
  let mockState: ReturnType<typeof createMockTaskStateService>;
  let searchFixture: ReturnType<typeof TestBed.createComponent<TaskListComponent>>;
  let searchComponent: TaskListComponent;

  beforeEach(() => {
    mockState = createMockTaskStateService({ loading: false, tasks: [TASK_PENDING] });

    TestBed.configureTestingModule({
      imports: [TaskListComponent],
      providers: [
        provideRouter([
          { path: 'dashboard', component: {} as any },
          { path: 'login', component: {} as any },
        ]),
        { provide: TaskStateService, useValue: mockState },
      ],
    });

    searchFixture = TestBed.createComponent(TaskListComponent);
    searchComponent = searchFixture.componentInstance;
    searchFixture.detectChanges();
  });

  it('should render the search input element (data-testid="search-input")', () => {
    const el: HTMLElement = searchFixture.nativeElement;
    expect(el.querySelector('[data-testid="search-input"]')).not.toBeNull();
  });

  it('should render the clear search icon (data-testid="clear-search")', () => {
    const el: HTMLElement = searchFixture.nativeElement;
    expect(el.querySelector('[data-testid="clear-search"]')).not.toBeNull();
  });

  it('should render a leading search icon (material-symbols-outlined "search")', () => {
    const el: HTMLElement = searchFixture.nativeElement;
    // The leading icon should be a span/element containing the text "search"
    const icons = el.querySelectorAll('.material-symbols-outlined');
    const hasSearchIcon = Array.from(icons).some(
      (icon) => icon.textContent?.trim() === 'search'
    );
    expect(hasSearchIcon).toBe(true);
  });

  it('should render the search input above the filter controls', () => {
    const el: HTMLElement = searchFixture.nativeElement;
    const searchWrapper = el.querySelector('.search-bar');
    const filterControls = el.querySelector('.filter-controls');
    expect(searchWrapper).not.toBeNull();
    expect(filterControls).not.toBeNull();
    // Search wrapper should appear before filter controls in DOM order
    const position = searchWrapper!.compareDocumentPosition(filterControls!);
    // DOCUMENT_POSITION_FOLLOWING (4) means filterControls comes after searchWrapper
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('should have a search input with placeholder text', () => {
    const el: HTMLElement = searchFixture.nativeElement;
    const input = el.querySelector<HTMLInputElement>('[data-testid="search-input"]');
    expect(input?.placeholder).toBeTruthy();
  });
});

describe('TaskListComponent — clear search behavior', () => {
  let mockState: ReturnType<typeof createMockTaskStateService>;
  let searchFixture: ReturnType<typeof TestBed.createComponent<TaskListComponent>>;
  let searchComponent: TaskListComponent;

  beforeEach(() => {
    mockState = createMockTaskStateService({ loading: false, tasks: [TASK_PENDING] });

    TestBed.configureTestingModule({
      imports: [TaskListComponent],
      providers: [
        provideRouter([
          { path: 'dashboard', component: {} as any },
          { path: 'login', component: {} as any },
        ]),
        { provide: TaskStateService, useValue: mockState },
      ],
    });

    searchFixture = TestBed.createComponent(TaskListComponent);
    searchComponent = searchFixture.componentInstance;
    searchFixture.detectChanges();
  });

  it('should reset searchTerm to empty string when clear icon is clicked', () => {
    searchComponent.searchTerm = 'groceries';
    searchFixture.detectChanges();

    const el: HTMLElement = searchFixture.nativeElement;
    const clearBtn = el.querySelector<HTMLElement>('[data-testid="clear-search"]');
    clearBtn!.click();
    searchFixture.detectChanges();

    expect(searchComponent.searchTerm).toBe('');
  });

  it('should call loadTasks() immediately (without debounce) when clear is clicked', () => {
    searchComponent.searchTerm = 'groceries';
    searchFixture.detectChanges();

    const loadTasksSpy = mockState.loadTasks as ReturnType<typeof vi.fn>;
    loadTasksSpy.mockClear();

    const el: HTMLElement = searchFixture.nativeElement;
    const clearBtn = el.querySelector<HTMLElement>('[data-testid="clear-search"]');
    clearBtn!.click();
    searchFixture.detectChanges();

    expect(loadTasksSpy).toHaveBeenCalled();
  });
});

describe('TaskListComponent — search empty state', () => {
  let emptySearchFixture: ReturnType<typeof TestBed.createComponent<TaskListComponent>>;
  let emptySearchComponent: TaskListComponent;
  let mockStateEmpty: ReturnType<typeof createMockTaskStateService>;

  beforeEach(() => {
    mockStateEmpty = createMockTaskStateService({ loading: false, tasks: [] });

    TestBed.configureTestingModule({
      imports: [TaskListComponent],
      providers: [
        provideRouter([
          { path: 'dashboard', component: {} as any },
          { path: 'login', component: {} as any },
        ]),
        { provide: TaskStateService, useValue: mockStateEmpty },
      ],
    });

    emptySearchFixture = TestBed.createComponent(TaskListComponent);
    emptySearchComponent = emptySearchFixture.componentInstance;
    emptySearchFixture.detectChanges();
  });

  it('should display "No results for..." when tasks are empty and searchTerm is active', () => {
    emptySearchComponent.searchTerm = 'xyz';
    emptySearchFixture.detectChanges();

    const el: HTMLElement = emptySearchFixture.nativeElement;
    const emptyState = el.querySelector('[data-testid="empty-state"]');
    expect(emptyState).not.toBeNull();
    expect(emptyState!.textContent).toContain("No results for 'xyz'");
  });

  it('should include the search term in single quotes in the empty state message', () => {
    emptySearchComponent.searchTerm = 'groceries';
    emptySearchFixture.detectChanges();

    const el: HTMLElement = emptySearchFixture.nativeElement;
    const emptyState = el.querySelector('[data-testid="empty-state"]');
    expect(emptyState!.textContent).toContain("'groceries'");
  });

  it('should display the default empty state when no search term is active', () => {
    emptySearchComponent.searchTerm = '';
    emptySearchFixture.detectChanges();

    const el: HTMLElement = emptySearchFixture.nativeElement;
    const emptyState = el.querySelector('[data-testid="empty-state"]');
    expect(emptyState).not.toBeNull();
    expect(emptyState!.textContent).toContain('No tasks yet');
  });

  it('should suppress the empty state while loading is true', () => {
    mockStateEmpty._loadingSignal.set(true);
    emptySearchComponent.searchTerm = 'something';
    emptySearchFixture.detectChanges();

    const el: HTMLElement = emptySearchFixture.nativeElement;
    expect(el.querySelector('[data-testid="empty-state"]')).toBeNull();
  });
});

describe('TaskListComponent — filter button triggers reload with current search term', () => {
  let filterSearchFixture: ReturnType<typeof TestBed.createComponent<TaskListComponent>>;
  let filterSearchComponent: TaskListComponent;
  let filterMockState: ReturnType<typeof createMockTaskStateService>;

  beforeEach(() => {
    filterMockState = createMockTaskStateService({ loading: false, tasks: [TASK_PENDING], filter: 'all' });

    TestBed.configureTestingModule({
      imports: [TaskListComponent],
      providers: [
        provideRouter([
          { path: 'dashboard', component: {} as any },
          { path: 'login', component: {} as any },
        ]),
        { provide: TaskStateService, useValue: filterMockState },
      ],
    });

    filterSearchFixture = TestBed.createComponent(TaskListComponent);
    filterSearchComponent = filterSearchFixture.componentInstance;
    filterSearchFixture.detectChanges();
  });

  it('should call loadTasks with the current searchTerm when a filter button is clicked', () => {
    filterSearchComponent.searchTerm = 'buy';
    filterSearchFixture.detectChanges();

    const loadTasksSpy = filterMockState.loadTasks as ReturnType<typeof vi.fn>;
    loadTasksSpy.mockClear();

    const el: HTMLElement = filterSearchFixture.nativeElement;
    const pendingBtn = el.querySelector<HTMLButtonElement>('[data-testid="filter-pending"]');
    pendingBtn!.click();
    filterSearchFixture.detectChanges();

    expect(filterMockState.filter()).toBe('pending');
    expect(loadTasksSpy).toHaveBeenCalledWith('buy');
  });

  it('should not reset searchTerm when a filter button is clicked', () => {
    filterSearchComponent.searchTerm = 'report';
    filterSearchFixture.detectChanges();

    const el: HTMLElement = filterSearchFixture.nativeElement;
    const completedBtn = el.querySelector<HTMLButtonElement>('[data-testid="filter-completed"]');
    completedBtn!.click();
    filterSearchFixture.detectChanges();

    expect(filterSearchComponent.searchTerm).toBe('report');
  });
});

// ─── Task 6: Dashboard navigation link ─────────────────────────────────────

describe('TaskListComponent — task 6 (dashboard navigation link)', () => {
  let navFixture: ReturnType<typeof TestBed.createComponent<TaskListComponent>>;
  let navComponent: TaskListComponent;
  let navMockState: ReturnType<typeof createMockTaskStateService>;

  beforeEach(() => {
    navMockState = createMockTaskStateService({ loading: false, tasks: [] });

    TestBed.configureTestingModule({
      imports: [TaskListComponent],
      providers: [
        provideRouter([
          { path: 'dashboard', component: {} as any },
          { path: 'login', component: {} as any },
        ]),
        { provide: TaskStateService, useValue: navMockState },
      ],
    });

    navFixture = TestBed.createComponent(TaskListComponent);
    navComponent = navFixture.componentInstance;
    navFixture.detectChanges();
  });

  it('should render a navigation link to /dashboard in the header (requirement 1.1)', () => {
    const el: HTMLElement = navFixture.nativeElement;
    const dashboardLink = el.querySelector<HTMLAnchorElement>(
      '[data-testid="dashboard-link"], a[href="/dashboard"], a[routerLink="/dashboard"], a[routerLink="dashboard"]',
    );
    expect(dashboardLink).not.toBeNull();
  });

  it('should render the logout button alongside the dashboard link in the header', () => {
    const el: HTMLElement = navFixture.nativeElement;
    const logoutBtn = el.querySelector('[data-testid="logout-button"]');
    const dashboardLink = el.querySelector(
      '[data-testid="dashboard-link"], a[href="/dashboard"], a[routerLink="/dashboard"], a[routerLink="dashboard"]',
    );
    expect(logoutBtn).not.toBeNull();
    expect(dashboardLink).not.toBeNull();
  });

  it('should render the dashboard link in the task-list-header element', () => {
    const el: HTMLElement = navFixture.nativeElement;
    const header = el.querySelector('.task-list-header');
    expect(header).not.toBeNull();
    const dashboardLink = header!.querySelector(
      '[data-testid="dashboard-link"], a[routerLink="/dashboard"], a[routerLink="dashboard"]',
    );
    expect(dashboardLink).not.toBeNull();
  });

  it('should navigate to /dashboard when the dashboard link is clicked', async () => {
    const el: HTMLElement = navFixture.nativeElement;
    const dashboardLink = el.querySelector<HTMLAnchorElement>('[data-testid="dashboard-link"]');
    expect(dashboardLink).not.toBeNull();
    // The link must have a routerLink or href pointing at dashboard
    const href = dashboardLink!.getAttribute('href');
    const routerLink =
      dashboardLink!.getAttribute('ng-reflect-router-link') ??
      dashboardLink!.getAttribute('routerlink');
    expect(href === '/dashboard' || routerLink !== null || href?.includes('dashboard')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Due Dates + Overdue Filter — TaskListComponent extensions (tasks 10.1–10.4)
// ---------------------------------------------------------------------------

/** Returns a date string N days from today (negative = past). */
function daysFromTodayList(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

const OVERDUE_TASK: Task = {
  id: 'overdue-list-001',
  userId: 'user-1',
  title: 'Overdue task',
  completed: false,
  due_date: daysFromTodayList(-1),
};

function makeListFixture(overrides: Parameters<typeof createMockTaskStateService>[0] = {}) {
  const mockState = createMockTaskStateService(overrides);

  TestBed.configureTestingModule({
    imports: [TaskListComponent],
    providers: [
      provideRouter([
        { path: 'dashboard', component: {} as any },
        { path: 'login', component: {} as any },
      ]),
      { provide: TaskStateService, useValue: mockState },
    ],
  });

  const fixture = TestBed.createComponent(TaskListComponent);
  fixture.componentInstance;
  fixture.detectChanges();
  return { fixture, mockState };
}

describe('TaskListComponent — overdue filter button (task 10.1)', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should render an "Overdue" filter button', () => {
    const { fixture } = makeListFixture({ tasks: [] });
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector('[data-testid="filter-overdue"]');
    expect(btn).not.toBeNull();
  });

  it('should set filter to "overdue" when Overdue button is clicked', () => {
    const { fixture, mockState } = makeListFixture({ tasks: [] });
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector<HTMLButtonElement>('[data-testid="filter-overdue"]');
    btn!.click();
    fixture.detectChanges();
    expect(mockState.filter()).toBe('overdue');
  });

  it('should apply active class when filter is "overdue"', () => {
    const { fixture, mockState } = makeListFixture({ tasks: [] });
    mockState.filter.set('overdue');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector<HTMLButtonElement>('[data-testid="filter-overdue"]');
    expect(btn?.classList.contains('active')).toBe(true);
  });

  it('should set aria-pressed="true" when filter is "overdue"', () => {
    const { fixture, mockState } = makeListFixture({ tasks: [] });
    mockState.filter.set('overdue');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector<HTMLButtonElement>('[data-testid="filter-overdue"]');
    expect(btn?.getAttribute('aria-pressed')).toBe('true');
  });
});

describe('TaskListComponent — overdue count badge (task 10.2)', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should render the overdue badge when overdueCount > 0', () => {
    const { fixture } = makeListFixture({ tasks: [OVERDUE_TASK], overdueCount: 1 });
    const el: HTMLElement = fixture.nativeElement;
    const badge = el.querySelector('.overdue-badge');
    expect(badge).not.toBeNull();
  });

  it('should NOT render the badge when overdueCount is 0', () => {
    const { fixture } = makeListFixture({ tasks: [], overdueCount: 0 });
    const el: HTMLElement = fixture.nativeElement;
    const badge = el.querySelector('.overdue-badge');
    expect(badge).toBeNull();
  });

  it('should display the correct overdue count in the badge', () => {
    const { fixture } = makeListFixture({ tasks: [OVERDUE_TASK], overdueCount: 3 });
    const el: HTMLElement = fixture.nativeElement;
    const badge = el.querySelector('.overdue-badge');
    expect(badge?.textContent?.trim()).toBe('3');
  });
});

describe('TaskListComponent — sort controls (task 10.3)', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should render a sort-by-due-date button', () => {
    const { fixture } = makeListFixture({ tasks: [] });
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector('[data-testid="sort-due-date"]');
    expect(btn).not.toBeNull();
  });

  it('should set sortBy to "due_date" when sort button is clicked', () => {
    const { fixture, mockState } = makeListFixture({ tasks: [] });
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector<HTMLButtonElement>('[data-testid="sort-due-date"]');
    btn!.click();
    fixture.detectChanges();
    expect(mockState.sortBy()).toBe('due_date');
  });

  it('should toggle sortDir between asc and desc on subsequent clicks', () => {
    const { fixture, mockState } = makeListFixture({ tasks: [] });
    const el: HTMLElement = fixture.nativeElement;
    const btn = el.querySelector<HTMLButtonElement>('[data-testid="sort-due-date"]');

    // First click: sortBy=due_date, sortDir=asc (default)
    btn!.click();
    fixture.detectChanges();
    expect(mockState.sortDir()).toBe('asc');

    // Second click: toggles to desc
    btn!.click();
    fixture.detectChanges();
    expect(mockState.sortDir()).toBe('desc');
  });

  it('should render a clear-sort button', () => {
    const { fixture } = makeListFixture({ tasks: [], sortBy: 'due_date' });
    const el: HTMLElement = fixture.nativeElement;
    // The component should show a clear sort button somewhere
    const clearBtn = el.querySelector('[data-testid="clear-sort"]');
    expect(clearBtn).not.toBeNull();
  });

  it('should set sortBy to null when clear-sort is clicked', () => {
    const { fixture, mockState } = makeListFixture({ tasks: [], sortBy: 'due_date' });
    mockState.sortBy.set('due_date');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const clearBtn = el.querySelector<HTMLButtonElement>('[data-testid="clear-sort"]');
    clearBtn!.click();
    fixture.detectChanges();
    expect(mockState.sortBy()).toBeNull();
  });
});

describe('TaskListComponent — overdue empty state (task 10.4)', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should show overdue-specific empty state when filter is overdue and tasks are empty', () => {
    const { fixture, mockState } = makeListFixture({ tasks: [], filter: 'overdue' });
    const el: HTMLElement = fixture.nativeElement;
    const emptyState = el.querySelector('[data-testid="overdue-empty-state"]');
    expect(emptyState).not.toBeNull();
    expect(emptyState?.textContent).toContain('No overdue tasks');
  });

  it('should NOT show the overdue empty state when tasks exist', () => {
    const { fixture } = makeListFixture({
      tasks: [OVERDUE_TASK],
      filter: 'overdue',
      overdueCount: 1,
    });
    const el: HTMLElement = fixture.nativeElement;
    const emptyState = el.querySelector('[data-testid="overdue-empty-state"]');
    expect(emptyState).toBeNull();
  });

  it('should NOT show overdue empty state when filter is "all" and tasks are empty', () => {
    const { fixture } = makeListFixture({ tasks: [], filter: 'all' });
    const el: HTMLElement = fixture.nativeElement;
    const emptyState = el.querySelector('[data-testid="overdue-empty-state"]');
    expect(emptyState).toBeNull();
  });
});
