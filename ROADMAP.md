# Todo App — Feature Roadmap

> Priorities ranked by value-to-effort ratio. Each feature is broken down into discrete backend and frontend tasks.

---

## Priority 1 — Search

**Goal:** Let users find tasks instantly by keyword across all their tasks.

**Why first:** Zero new models, one query param, one UI element. Delivers immediate value once a user has more than ~20 tasks and costs the least of all five features.

**Status:** ✅ Spec ready — `.sdd/specs/search/`

### Backend

- [x] Add optional `q: str | None` query parameter to `GET /api/v1/tasks`
- [x] Update `TaskRepository.list_by_user()` to accept an optional `search` argument
- [x] Implement case-insensitive `LIKE %keyword%` filter on the `title` column (chain with existing `status` filter)
- [x] Update `TaskService.list_tasks()` to pass `search` down to the repository
- [x] Add unit tests for the repository search filter (empty query, partial match, case-insensitive, no results)
- [x] Update `TaskListResponse` schema if needed (no change expected)

### Frontend

- [x] Add `search` signal (`string`, default `''`) to `TaskStateService`
- [x] Extend `TaskApiService.listTasks()` to accept and forward the `q` parameter
- [x] Update `loadTasks()` in `TaskStateService` to pass the current search term
- [x] Add a debounced search input above the filter buttons in `TaskListComponent` (300 ms debounce via `RxJS debounceTime`)
- [x] Wire input value changes to call `loadTasks()` so results update as the user types
- [x] Show "No results for '...'" empty state when search returns zero tasks
- [x] Clear search when filter tab changes (or keep them independent — decide before implementation)
- [x] Add `data-testid="search-input"` and cover with e2e test (type keyword → list filters)

---

## Priority 2 — Due Dates + Overdue Filter

**Goal:** Allow users to assign a deadline to each task and surface overdue items prominently.

**Why second:** Due dates are the most-requested feature in any todo app. The `created_at` column already proves the DB supports dates; adding `due_date` is a one-migration change.

### Backend

- [X] Add `due_date: DATETIME | NULL` column to the `tasks` table via a new Alembic migration
- [X] Update `TaskResponse` schema: add optional `due_date: datetime | None`
- [X] Update `CreateTaskRequest` schema: add optional `due_date: datetime | None`
- [X] Update `UpdateTaskRequest` schema: add optional `due_date: datetime | None`
- [X] Update `TaskService.create_task()` to accept and persist `due_date`
- [X] Update `TaskService.update_task()` to accept and persist `due_date`
- [X] Add `overdue` option to the status filter: tasks where `due_date < now()` AND `completed = false`
- [X] Update `TaskRepository.list_by_user()` to handle the new `overdue` filter variant
- [X] Add unit tests: create with due date, update due date, overdue filter returns correct rows

### Frontend

- [X] Add `due_date` field to the `Task` model (`string | null`, ISO 8601)
- [X] Add a date picker input to `TaskItemComponent` edit mode (use `<input type="date">`)
- [X] Show due date as a subtle label below the task title when set (`due: Apr 10`)
- [X] Highlight overdue tasks with a red/orange accent (CSS class `task--overdue` applied when `due_date < today && !completed`)
- [X] Add "Overdue" button to the filter controls in `TaskListComponent`
- [X] Update `TaskApiService.updateTask()` to send `due_date` in the request body
- [X] Update `TaskStateService` filter type: `'all' | 'pending' | 'completed' | 'overdue'`
- [X] Update computed `tasks` signal to handle the `overdue` filter client-side
- [X] Add e2e tests: set due date → displayed, overdue task gets red styling, overdue filter works

---

## Priority 3 — Labels / Categories

**Goal:** Let users organize tasks into color-coded labels (e.g. Work, Personal, Shopping).

**Why third:** This is the feature that graduates the app from a tutorial to a real productivity tool. It replaces the flat list with a structured, scannable view.

### Backend

- [ ] Create `labels` table: `{ id: UUID PK, user_id: UUID FK, name: VARCHAR(50), color: VARCHAR(7) }` — color stored as hex string
- [ ] Create `task_labels` join table: `{ task_id: UUID FK, label_id: UUID FK }` (composite PK)
- [ ] Write Alembic migration for both tables
- [ ] Create `LabelRepository`: `create()`, `list_by_user()`, `get_by_id()`, `update()`, `delete()`
- [ ] Create `LabelService`: business logic + ownership checks (user can only manage their own labels)
- [ ] Create `LabelRouter` at `/api/v1/labels`:
  - `POST /api/v1/labels` → 201 LabelResponse
  - `GET /api/v1/labels` → 200 LabelListResponse
  - `PUT /api/v1/labels/{label_id}` → 200 LabelResponse
  - `DELETE /api/v1/labels/{label_id}` → 200 MessageResponse
- [ ] Add `label_ids: list[UUID]` to `CreateTaskRequest` and `UpdateTaskRequest`
- [ ] Update `TaskResponse` to include `labels: list[LabelResponse]`
- [ ] Update `TaskService` to handle label assignment on create/update (with ownership check)
- [ ] Add optional `label_id` query parameter to `GET /api/v1/tasks` for filtering by label
- [ ] Add unit tests for label CRUD and task–label assignment

### Frontend

- [ ] Create `Label` model: `{ id, userId, name, color }`
- [ ] Create `LabelApiService` with full CRUD methods
- [ ] Create `LabelStateService` to hold the user's label list as a signal
- [ ] Load labels on app init (or lazily on task list load)
- [ ] Add a label management section to the Dashboard page (create/rename/delete labels with color picker)
- [ ] Add label badge(s) to `TaskItemComponent` — colored pill with label name
- [ ] Add label selector (multi-select dropdown) to task create form and task edit mode
- [ ] Add label filter chips to `TaskListComponent` (below the All/Pending/Completed buttons)
- [ ] Update `TaskStateService` to support filtering by `label_id` (pass to API or compute client-side)
- [ ] Add e2e tests: create label, assign to task, filter by label, delete label

---

## Priority 4 — Subtasks

**Goal:** Allow users to break a task into a checklist of smaller steps, with a progress bar on the parent card.

**Why fourth:** High visual impact — the progress bar makes every task feel actionable. It is the most visible differentiator from a basic todo list.

### Backend

- [ ] Create `subtasks` table: `{ id: UUID PK, task_id: UUID FK CASCADE, title: VARCHAR(255), completed: BOOLEAN default FALSE, position: INTEGER, created_at: DATETIME }`
- [ ] Write Alembic migration
- [ ] Create `SubtaskRepository`: `create()`, `list_by_task()`, `get_by_id()`, `update()`, `toggle()`, `delete()`, `reorder()`
- [ ] Create `SubtaskService` with ownership check (verify parent task belongs to current user)
- [ ] Create `SubtaskRouter` nested under tasks at `/api/v1/tasks/{task_id}/subtasks`:
  - `POST /api/v1/tasks/{task_id}/subtasks` → 201 SubtaskResponse
  - `GET /api/v1/tasks/{task_id}/subtasks` → 200 SubtaskListResponse
  - `PUT /api/v1/tasks/{task_id}/subtasks/{subtask_id}` → 200 SubtaskResponse
  - `PATCH /api/v1/tasks/{task_id}/subtasks/{subtask_id}/toggle` → 200 SubtaskResponse
  - `DELETE /api/v1/tasks/{task_id}/subtasks/{subtask_id}` → 200 MessageResponse
- [ ] Update `TaskResponse` to include `subtask_count: int` and `completed_subtask_count: int` (avoid eager-loading full subtask list in the task list endpoint)
- [ ] Add unit tests for subtask CRUD and ownership enforcement

### Frontend

- [ ] Create `Subtask` model: `{ id, taskId, title, completed, position }`
- [ ] Update `Task` model to include `subtaskCount: number` and `completedSubtaskCount: number`
- [ ] Create `SubtaskApiService` with full CRUD + toggle methods
- [ ] Add progress bar to `TaskItemComponent` when `subtaskCount > 0` — renders as `2 / 5` text and a `<progress>` element
- [ ] Add expand/collapse toggle to `TaskItemComponent` to show/hide the subtask list
- [ ] Create `SubtaskItemComponent` (inline edit, checkbox, delete)
- [ ] Add "Add subtask" inline input at the bottom of the expanded subtask list
- [ ] Create `SubtaskStateService` (or extend `TaskStateService`) to hold subtasks per task, with optimistic toggle and delete
- [ ] Auto-mark parent task as completed when all subtasks are completed (optional prompt to user)
- [ ] Add e2e tests: expand task → add subtask → check subtask → progress bar updates → all checked → parent auto-completes

---

## Priority 5 — Statistics Dashboard

**Goal:** Turn the Account page into a productivity insights page — tasks completed this week, completion rate, and average completion time.

**Why fifth:** Reuses the existing Dashboard page and all existing data. Adds no new models (only a new `completed_at` timestamp) and makes the app feel data-driven.

### Backend

- [ ] Add `completed_at: DATETIME | NULL` column to `tasks` table via Alembic migration
- [ ] Update `TaskService.toggle_completion()` to set `completed_at = now()` when completing and `NULL` when reopening
- [ ] Create `StatsRouter` at `/api/v1/stats`:
  - `GET /api/v1/stats/summary` → `StatsResponse`
    - `total_tasks: int`
    - `completed_tasks: int`
    - `pending_tasks: int`
    - `completed_this_week: int`
    - `completed_last_week: int`
    - `completion_rate: float` (percentage)
    - `avg_completion_hours: float | None` (avg time from `created_at` to `completed_at`)
- [ ] Create `StatsService` with pure query logic using SQLAlchemy aggregates (`func.count`, `func.avg`, date range filters)
- [ ] Add unit tests for all stats calculations (including edge cases: no tasks, all pending, no completions this week)

### Frontend

- [ ] Create `Stats` model matching `StatsResponse`
- [ ] Create `StatsApiService` with a `getSummary()` method
- [ ] Redesign `DashboardComponent` layout: top section keeps the account/password form; bottom section shows stats cards
- [ ] Build stat cards:
  - Total / Pending / Completed counts
  - "This week vs last week" completed tasks with a trend arrow (up/down)
  - Completion rate as a circular progress indicator (CSS-only or SVG)
  - Average completion time (e.g. "avg 1.4 days")
- [ ] Load stats on `DashboardComponent` init, show skeleton loaders while fetching
- [ ] Refresh stats after password change completes (stats stay visible, only the form resets)
- [ ] Add `data-testid` attributes to all stat values and cover with e2e tests

---

## Summary

| # | Feature | New DB Tables | New API Endpoints | Effort |
|---|---------|--------------|------------------|--------|
| 1 | Search | None | 0 (extends existing) | Small |
| 2 | Due Dates + Overdue | 1 column on `tasks` | 0 (extends existing) | Small |
| 3 | Labels / Categories | `labels`, `task_labels` | 4 label endpoints | Medium |
| 4 | Subtasks | `subtasks` | 5 subtask endpoints | Medium |
| 5 | Statistics Dashboard | 1 column on `tasks` | 1 stats endpoint | Medium |
