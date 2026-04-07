# Research Notes: Due Dates + Overdue Filter

## Investigation Summary

**Discovery type**: Light (extension of existing system)
**Date**: 2026-04-06

---

## Existing Codebase Patterns

### Backend

- **ORM**: SQLAlchemy 2.x with `Mapped`/`mapped_column` declarative style (see `backend/app/models/task.py`). New columns follow the same pattern; `due_date` will use `Mapped[Optional[datetime]]` with `nullable=True`.
- **Migrations**: Alembic, single linear chain (`001_initial_schema.py` → new `002_add_due_date.py`). The pattern is `op.add_column` / `op.drop_column` for additive migrations.
- **Schemas**: Pydantic v2 `BaseModel` with `model_config = {"from_attributes": True}` on response models. Optional fields are typed `Optional[X] = None`.
- **Router**: FastAPI `Query` parameters with `alias` pattern already used for `status_filter`. The same technique applies for `sort_by` and `sort_dir`.
- **Service layer**: All business logic validated in `TaskService`; repository is a thin persistence adapter. Sorting logic will live in the repository (SQL `ORDER BY`) and filtering (overdue) in the service as a computed property.
- **Ownership pattern**: `_get_owned_task` guards all mutations. No change needed for due-date mutations — they go through the existing `update_task` path.

### Frontend

- **State management**: Angular signals (`signal`, `computed`) in `TaskStateService`. The `filter` signal is already a writable signal with values `'all' | 'pending' | 'completed'`; extending the union to include `'overdue'` is the natural pattern.
- **Task model**: Plain TypeScript interface in `frontend/src/app/shared/models/task.model.ts`. Adding `due_date?: string | null` follows the existing optional field convention.
- **API service**: `HttpParams` builder pattern in `TaskApiService.listTasks()`. Extending it to accept `sort_by` and `sort_dir` fits the existing chain.
- **Components**: Both `TaskListComponent` and `TaskItemComponent` are standalone, using `CommonModule` + `FormsModule`. No routing changes required.
- **Overdue detection**: Must be purely client-side computed (`computed()` signal). No dedicated backend endpoint is needed; the backend already returns all fields needed (`due_date`, `completed`).

---

## Key Technical Decisions

### 1. Overdue Detection: Client-side vs Backend-side

**Decision**: Client-side via Angular `computed()` signals.

**Rationale**:
- Overdue status is a function of `due_date < today && !completed`, computable from existing task fields.
- No new API endpoint or query parameter needed.
- The Angular signals model makes it natural to derive `overdueCount` and `overdueFilter` from the task array reactively.
- A separate backend `/overdue` endpoint would duplicate filtering logic and add unnecessary round-trips.

### 2. Sorting: Backend vs Frontend

**Decision**: Backend sorting via SQL `ORDER BY`, exposed as `sort_by=due_date&sort_dir=asc|desc` query parameters.

**Rationale**: Requirement 6.2 explicitly mandates backend sorting. SQLAlchemy supports `nullslast()` ordering, which satisfies requirement 6.7 (tasks without due date go last).

### 3. `due_date` wire format

**Decision**: ISO 8601 date string (`YYYY-MM-DD`) in JSON; stored as `DATETIME NULL` in the database (time component always midnight UTC or ignored).

**Rationale**:
- Consistent with existing `created_at` DateTime column.
- Angular's built-in `DatePipe` and `<input type="date">` both use `YYYY-MM-DD` natively.
- Avoids timezone complexity: comparisons are date-only (day granularity).
- Backend serializes with Pydantic's `Optional[date]` type (`datetime.date`), which serializes to `"YYYY-MM-DD"` automatically.

### 4. Overdue count badge: live update strategy

**Decision**: Angular `computed()` signal derived from the main `_tasks` signal.

**Rationale**: Any mutation that updates `_tasks` (toggle, update, delete, reload) automatically re-derives `overdueCount`. No polling or WebSocket required. Requirement 3.4 (auto-update without page reload) is satisfied because `computed()` re-evaluates on every signal write.

### 5. Alembic migration: additive, non-breaking

**Decision**: `op.add_column` with `nullable=True` and no server default.

**Rationale**: Existing rows will have `due_date = NULL`, which is the correct "no deadline" state. No data backfill needed. Downgrade uses `op.drop_column`.

---

## SQLAlchemy `nullslast` for sort_dir

SQLAlchemy provides `nullslast()` / `nullsfirst()` ordering functions in `sqlalchemy` module. Usage:

```python
from sqlalchemy import nullslast, asc, desc

query.order_by(nullslast(asc(Task.due_date)))   # ASC, NULLs last
query.order_by(nullslast(desc(Task.due_date)))  # DESC, NULLs last
```

This satisfies requirement 6.7 without application-level sorting.

---

## Angular `DatePipe` and `<input type="date">`

- `DatePipe` with format `'MMM d, y'` produces "Apr 10, 2026" — matches the example in requirement 2.3.
- `<input type="date">` returns and accepts `YYYY-MM-DD` strings, matching the wire format.
- Comparing `due_date` string to `new Date().toISOString().slice(0, 10)` gives a deterministic date-only comparison.

---

## Accessibility Findings

- `<input type="date">` is fully keyboard-navigable in all major browsers.
- Overdue indicator must use both color AND a non-color cue (icon + label) per requirement 7.1. A warning icon (e.g., `⚠`) with `aria-label="Overdue"` satisfies both requirements 7.1 and 7.2.
- Filter buttons must have `aria-pressed` to convey active state to screen readers.
- Sort controls must have `aria-label` describing the sort direction.
