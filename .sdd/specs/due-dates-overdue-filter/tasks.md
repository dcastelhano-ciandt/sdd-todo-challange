# Implementation Plan

## Phase 1 — Backend (TDD, sequential)

- [x] 1. Add due_date to database and ORM model
- [x] 1.1 Write failing tests for the Alembic migration (verify `due_date DATETIME NULL` column and `ix_tasks_userId_due_date` index exist after `upgrade head`; verify both are removed after `downgrade`)
  - Run the migration (`alembic upgrade head`) and confirm tests pass
  - _Requirements: 1_
- [x] 1.2 Extend the SQLAlchemy `Task` ORM model with `due_date: Mapped[Optional[date]]` using `mapped_column(DateTime, nullable=True, default=None)`
  - _Requirements: 1_

- [x] 2. Update Pydantic schemas to expose due_date
- [x] 2.1 Add `due_date: Optional[date] = None` to `CreateTaskRequest`, `UpdateTaskRequest`, and `TaskResponse`
  - Pydantic `date` type rejects malformed strings with 422 automatically, satisfying input validation at the API boundary
  - _Requirements: 1_

- [x] 3. Update TaskRepository to persist due_date and sort by it
- [x] 3.1 Write failing tests covering: `nullslast(asc)` ordering (tasks with a due date appear before NULL rows), `nullslast(desc)` ordering, fallback to `created_at DESC` when `sort_by` is `None`
  - _Requirements: 1, 6_
- [x] 3.2 Extend `TaskRepository.create` to accept and persist `due_date`
  - _Requirements: 1_
- [x] 3.3 Extend `TaskRepository.list_by_user` to accept `sort_by` and `sort_dir` parameters; apply `nullslast(asc(Task.due_date))` or `nullslast(desc(Task.due_date))` when `sort_by == "due_date"`; fall back to `created_at DESC` otherwise
  - _Requirements: 6_

- [x] 4. Update TaskService to thread due_date and sort parameters through
- [x] 4.1 Extend `TaskService.create_task` and `TaskService.update_task` to accept and forward `due_date`; ensure `due_date=None` explicitly clears the field on update
  - _Requirements: 1_
- [x] 4.2 Extend `TaskService.list_tasks` to accept `sort_by` and `sort_dir`; validate both against an allowlist (`sort_by`: `None` or `"due_date"`; `sort_dir`: `"asc"` or `"desc"`) and raise `ValidationError` on unknown values before forwarding to the repository
  - _Requirements: 6_

- [x] 5. Update TaskRouter to accept new query and body parameters
- [x] 5.1 Add `sort_by: Literal["due_date"] | None` and `sort_dir: Literal["asc", "desc"] = "asc"` query parameters to `GET /api/v1/tasks`; forward both to `TaskService.list_tasks`
  - Use `Literal` types so FastAPI rejects invalid values with 422 before reaching the service
  - _Requirements: 6_
- [x] 5.2 Forward `due_date` from `CreateTaskRequest` to `TaskService.create_task` on `POST /api/v1/tasks`, and from `UpdateTaskRequest` to `TaskService.update_task` on `PUT /api/v1/tasks/{id}`
  - _Requirements: 1_

---

## Phase 2 — Frontend (TDD, sequential)

- [x] 6. Extend the TypeScript Task model
- [x] 6.1 Add `due_date?: string | null` to the `Task` interface; add `CreateTaskRequest.due_date`, `UpdateTaskRequest.due_date`, and the `TaskSortBy` / `TaskSortDir` type aliases
  - _Requirements: 1, 2, 3_

- [x] 7. Update TaskApiService to send due_date and sort parameters
- [x] 7.1 Extend `TaskApiService.listTasks` to accept optional `sortBy` and `sortDir` parameters and append them as `HttpParams` when `sortBy` is set
  - _Requirements: 6_
- [x] 7.2 Extend `TaskApiService.createTask` and `TaskApiService.updateTask` to accept and include `dueDate` in the request body; send `null` explicitly when clearing
  - _Requirements: 1_

- [x] 8. Update TaskStateService with overdue derivation and sort state
- [x] 8.1 Write failing tests for: `overdueCount` increments for past-due incomplete tasks; `overdueCount` excludes completed tasks; `overdueCount` updates after `toggleCompletion`; `tasks()` with filter `'overdue'` returns only past-due incomplete tasks; returns empty array when none qualify
  - _Requirements: 3, 4, 5_
- [x] 8.2 Add `sortBy: WritableSignal<TaskSortBy>` (default `null`) and `sortDir: WritableSignal<TaskSortDir>` (default `'asc'`) writable signals; update `loadTasks()` to read and forward them to `TaskApiService.listTasks`
  - _Requirements: 6_
- [x] 8.3 Extend the `filter` signal type to include `'overdue'`; add an `isOverdue(task)` pure helper (`due_date != null && !completed && due_date < todayISO()`); add an `'overdue'` branch to the `tasks()` computed signal; add `overdueCount: Signal<number>` as `computed(() => _tasks().filter(isOverdue).length)`
  - _Requirements: 3, 4, 5_
- [x] 8.4 Extend `TaskStateService.createTask` and `TaskStateService.updateTask` to accept and forward `dueDate` to `TaskApiService`
  - _Requirements: 1_

- [x] 9. Update TaskItemComponent to display and edit due date
- [x] 9.1 In view mode, render the due date as a formatted label (`DatePipe 'MMM d, y'`) with `aria-label="Due: <date>"`; hide the label when `due_date` is absent; apply the overdue indicator (`class="overdue-indicator"`, warning icon, "Overdue" text, `aria-label="Overdue" role="img"`) and the `task--overdue` CSS class to the task item when `isOverdue(task)` is true
  - Non-color indicator (bold/underline + icon) ensures accessibility for color-vision-deficient users
  - _Requirements: 2, 3, 7_
- [x] 9.2 In edit mode, add `<input type="date">` bound to a local `editDueDate` field with `aria-label="Due date"`; display an inline validation error when the browser reports an invalid date; clearing the field submits `due_date: null`
  - Native `<input type="date">` provides full keyboard navigation without additional implementation
  - _Requirements: 1, 7_

- [x] 10. Update TaskListComponent with filter button, sort controls, badge, and empty state
- [x] 10.1 Add an "Overdue" filter button to the filter controls row; bind `[class.active]` and `[attr.aria-pressed]` to `taskState.filter() === 'overdue'`; clicking the button calls `taskState.filter.set('overdue')`; a second click (or any other filter button) resets the filter to restore the full list
  - _Requirements: 4_
- [x] 10.2 Render the `overdueCount` badge next to the "Overdue" button using `aria-live="polite"`; hide the badge with `*ngIf="taskState.overdueCount() > 0"`
  - _Requirements: 5_
- [x] 10.3 Add sort controls: a "Sort by due date" button that calls a `toggleDueDateSort()` helper (sets `sortBy('due_date')`, toggles `sortDir` between `'asc'` and `'desc'`, calls `loadTasks()`); render an ASC/DESC arrow indicator on the button when the sort is active; provide a "Clear sort" action that sets `sortBy(null)` and reloads tasks
  - _Requirements: 6_
- [x] 10.4 Render an overdue-specific empty-state message (`"No overdue tasks. You are all caught up!"`) when `taskState.tasks().length === 0 && taskState.filter() === 'overdue'`
  - _Requirements: 4_

---

## Phase 3 — Tests

- [x] 11. Backend integration tests
- [x]* 11.1 Test `POST /api/v1/tasks` with a valid `due_date`: verify 201 response includes the `due_date` field; verify 422 on a malformed date string
  - _Requirements: 1_
- [x]* 11.2 Test `PUT /api/v1/tasks/{id}` with `due_date=null`: verify response has `due_date: null`
  - _Requirements: 1_
- [x]* 11.3 Test `GET /api/v1/tasks?sort_by=due_date&sort_dir=asc`: verify tasks are ordered earliest-first with null values last
  - _Requirements: 6_
- [x]* 11.4 Test `GET /api/v1/tasks?sort_by=due_date&sort_dir=desc`: verify tasks are ordered latest-first with null values last
  - _Requirements: 6_
- [x]* 11.5 Test `GET /api/v1/tasks?sort_by=unknown`: verify 422 response
  - _Requirements: 6_

- [ ] 12. Frontend end-to-end tests
- [ ]* 12.1 Create a task with a due date and verify the due date label appears on the task card in `"MMM d, y"` format; edit the task to remove the due date and verify the label disappears
  - _Requirements: 1, 2_
- [ ]* 12.2 With a past-due incomplete task present, verify the overdue indicator (icon + "Overdue" text) is visible on the task item and the overdue badge shows the correct count
  - _Requirements: 3, 5_
- [ ]* 12.3 Activate the "Overdue" filter and verify only overdue tasks are shown and `aria-pressed="true"` is set on the button; deactivate the filter and verify the full list is restored
  - _Requirements: 4_
- [ ]* 12.4 Activate the "Overdue" filter when no overdue tasks exist and verify the overdue empty-state message is displayed
  - _Requirements: 4_
- [ ]* 12.5 Click "Sort by due date" and verify the API is called with `sort_by=due_date&sort_dir=asc`; click again to toggle to DESC and verify `sort_dir=desc`; click "Clear sort" and verify the sort is removed
  - _Requirements: 6_
- [ ]* 12.6 Set a due date using only keyboard navigation (Tab to focus, keyboard to pick date, Enter to save) and verify the field is reachable and submittable without a pointer device
  - _Requirements: 7_
