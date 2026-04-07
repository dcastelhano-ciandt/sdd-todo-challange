# Requirements Document

## Project Description (Input)
Search — Let users find tasks instantly by keyword across all their tasks. Backend: add optional 'q' query param to GET /api/v1/tasks, case-insensitive LIKE filter on title column. Frontend: debounced search input (300ms) above filter buttons, wire to loadTasks(), show 'No results for...' empty state. UI reference: frontend/src/ui/tasks_main_list_desktop, frontend/src/ui/tasks_empty_state_desktop

## Introduction

This document defines the requirements for the **Search** feature of the Task Flow task management application. The feature enables authenticated users to find tasks instantly by typing keywords into a dedicated search input. The search filters tasks by title in a case-insensitive manner and composes with the existing status filter. Both the backend API and the Angular frontend must be extended to support this capability.

## Requirements

### Requirement 1: Backend — Search Query Parameter

**Objective:** As an authenticated user, I want the task listing API to accept an optional search keyword, so that I can retrieve only tasks whose titles match my query.

#### Acceptance Criteria

1. The Tasks API shall accept an optional `q` query parameter on `GET /api/v1/tasks`.
2. When `q` is provided and non-empty, the Tasks API shall return only tasks whose title contains the value of `q` using a case-insensitive match.
3. When `q` is omitted or empty, the Tasks API shall return tasks without any title filter, preserving existing behavior.
4. When both `q` and `status` parameters are provided, the Tasks API shall apply both filters simultaneously, returning tasks that satisfy both conditions.
5. The Tasks API shall return an empty task list (not an error) when no tasks match the provided `q` value.
6. The Tasks API shall always restrict results to tasks owned by the authenticated user, regardless of the `q` parameter.

---

### Requirement 2: Backend — Repository Search Support

**Objective:** As a developer, I want the task repository to support title-based filtering, so that search queries can be executed efficiently at the database layer.

#### Acceptance Criteria

1. The Task Repository shall filter tasks using a SQL `LIKE` expression on the `title` column when a search keyword is provided.
2. The Task Repository shall apply the title filter in a case-insensitive manner (e.g., using `ILIKE` or `lower()` normalization).
3. The Task Repository shall chain the title filter with any existing `completed` status filter when both are present.
4. The Task Repository shall preserve the existing `ORDER BY created_at DESC` ordering when a search filter is applied.

---

### Requirement 3: Backend — Service Layer Search Propagation

**Objective:** As a developer, I want the task service to propagate the search keyword to the repository, so that the business logic layer correctly coordinates search with status filtering.

#### Acceptance Criteria

1. The Task Service `list_tasks` method shall accept an optional `q` parameter representing the search keyword.
2. When `q` is a non-empty string after stripping whitespace, the Task Service shall pass it to the repository as the title filter.
3. When `q` is `None`, an empty string, or whitespace-only, the Task Service shall pass `None` as the title filter to the repository (no title filtering applied).

---

### Requirement 4: Frontend — Search Input Component

**Objective:** As a user, I want a visible search input field above the status filter buttons in the task list view, so that I can type keywords to find tasks.

#### Acceptance Criteria

1. The Task List Component shall render a text input field above the status filter buttons.
2. The search input shall display placeholder text that communicates its purpose (e.g., "Search tasks...").
3. The search input shall include a leading search icon consistent with the application's design system.
4. The search input shall include a clear/close icon that, when clicked, resets the search term to empty.
5. When the clear icon is clicked, the Task List Component shall reload all tasks without a search filter.
6. The Task List Component shall be the owner of the search term state, initializing it as an empty string.

---

### Requirement 5: Frontend — Debounced Search Execution

**Objective:** As a user, I want the task list to update automatically as I type, without triggering excessive API requests, so that the search experience feels responsive and efficient.

#### Acceptance Criteria

1. When the user types in the search input, the Task List Component shall wait 300 milliseconds after the last keystroke before calling `loadTasks()`.
2. The Task List Component shall cancel any pending debounced call when a new keystroke occurs within the 300ms window.
3. When `loadTasks()` is called with a search term, the Task State Service shall pass the `q` parameter to the Task API Service.
4. The Task API Service shall include the `q` parameter as a query string on `GET /api/v1/tasks` requests when it is non-empty.
5. When the search input is cleared (empty string), the Task List Component shall call `loadTasks()` without a `q` parameter to restore the full task list.

---

### Requirement 6: Frontend — Search Empty State

**Objective:** As a user, I want to see a meaningful message when my search returns no results, so that I understand no matching tasks exist rather than mistaking it for an error.

#### Acceptance Criteria

1. When `loadTasks()` completes and the returned task list is empty and an active search term is present, the Task List Component shall display the message: `No results for '[search term]'`.
2. The search-specific empty state message shall include the exact keyword the user searched for, enclosed in single quotes.
3. When the task list is empty and no search term is active, the Task List Component shall display the default empty state message (e.g., "No tasks yet. Create your first task to get started.").
4. While tasks are loading (after a search keystroke debounce fires), the Task List Component shall display the loading indicator and suppress the empty state message.

---

### Requirement 7: Frontend — Search and Status Filter Composition

**Objective:** As a user, I want search and status filters to work together, so that I can narrow down tasks by both keyword and completion state simultaneously.

#### Acceptance Criteria

1. When both a search term and a status filter are active, the Task State Service shall pass both `q` and `status` parameters to the Task API Service in a single request.
2. When the user changes the status filter while a search term is active, the Task List Component shall re-execute `loadTasks()` with both the current search term and the new status filter.
3. When the user changes the search term while a status filter is active, the debounce mechanism shall apply and the subsequent `loadTasks()` call shall include both the current status filter and the updated search term.
4. The Task List Component shall not reset the status filter when the search input changes, and shall not reset the search term when the status filter changes.
