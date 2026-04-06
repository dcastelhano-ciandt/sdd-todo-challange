# Requirements Document

## Introduction

This document defines the requirements for a full-featured Todo application consisting of a FastAPI backend and an Angular frontend. The application supports user registration, authentication, and task management. All code is organized into two top-level directories: `backend/` for the FastAPI service and `frontend/` for the Angular application.

## Data Model

### SQLite Database Schema

**Table: tasks** — Todo tasks

| Column | Type | Description |
|---|---|---|
| id | UUID | Task ID (primary key) |
| userId | UUID | Task owner (foreign key → users) |
| title | VARCHAR | Task title |
| completed | BOOLEAN | Completion status |

## Requirements

### Requirement 1: User Registration

**Objective:** As a new visitor, I want to create an account with my email and password, so that I can access the application and manage my own tasks.

#### Acceptance Criteria

1. When a visitor submits a registration form with a valid email address and a password that meets complexity rules, the Todo App shall create a new user account and return a success response.
2. If the submitted email address is already associated with an existing account, the Todo App shall reject the registration request and return an error message indicating the email is already in use.
3. If the submitted email address is malformed or the password does not meet the minimum length requirement, the Todo App shall reject the request and return a validation error describing the specific constraint that was violated.
4. The Todo App shall store passwords as a securely hashed value and never persist or expose plaintext passwords.
5. When a new user account is successfully created, the Todo App shall respond with an authentication token so the user can immediately begin using the application without a separate login step.

---

### Requirement 2: User Authentication

**Objective:** As a registered user, I want to log in with my credentials, so that I can securely access my personal task list.

#### Acceptance Criteria

1. When a registered user submits valid credentials (email and password), the Todo App shall issue a JWT access token and return it to the client.
2. If the submitted credentials are invalid or the user account does not exist, the Todo App shall return an authentication error and shall not disclose whether the email or the password was incorrect.
3. The Todo App shall enforce token expiration and shall reject requests made with expired tokens.
4. While a user is authenticated, the Todo App shall associate all task operations exclusively with that user's account.
5. When an authenticated user requests to log out, the Todo App shall invalidate the session so that the previously issued token can no longer be used.

---

### Requirement 3: Task Creation

**Objective:** As an authenticated user, I want to create new tasks with a title, so that I can track the things I need to do.

#### Acceptance Criteria

1. When an authenticated user submits a new task with at least a non-empty title, the Todo App shall persist the task and associate it with the authenticated user's `userId`.
2. If a task submission contains an empty or missing title, the Todo App shall reject the request and return a validation error.
3. The Todo App shall assign a UUID as the task `id` at the time of creation and set `completed` to `false` by default.
4. When a task is successfully created, the Todo App shall return the full task object (`id`, `userId`, `title`, `completed`).

---

### Requirement 4: Task Listing and Filtering

**Objective:** As an authenticated user, I want to view all my tasks and filter them by status, so that I can focus on what is pending or review what I have already completed.

#### Acceptance Criteria

1. When an authenticated user requests their task list, the Todo App shall return only the tasks belonging to that user, ordered by creation date descending by default.
2. The Todo App shall not include tasks belonging to other users in any task list response.
3. When a user applies a status filter (pending or completed), the Todo App shall return only the tasks matching the requested status.
4. While the task list is loading, the Angular Frontend shall display a loading indicator to the user.
5. If the user's task list is empty, the Angular Frontend shall display a descriptive empty-state message rather than a blank list.

---

### Requirement 5: Task Update

**Objective:** As an authenticated user, I want to edit the title of an existing task, so that I can keep task details accurate.

#### Acceptance Criteria

1. When an authenticated user submits an updated `title` for a task they own, the Todo App shall persist the change and return the updated task object (`id`, `userId`, `title`, `completed`).
2. If a user attempts to update a task that does not belong to them, the Todo App shall reject the request with an authorization error and shall not modify any data.
3. If the update payload contains an empty or missing `title`, the Todo App shall reject the request and return a validation error.

---

### Requirement 6: Task Completion Toggle

**Objective:** As an authenticated user, I want to mark tasks as complete or reopen them, so that I can track my progress.

#### Acceptance Criteria

1. When an authenticated user marks a pending task as complete, the Todo App shall set the task's `completed` field to `true`.
2. When an authenticated user marks a completed task as pending, the Todo App shall set the task's `completed` field to `false`.
3. If a user attempts to change the completion status of a task that does not belong to them, the Todo App shall reject the request with an authorization error.
4. The Angular Frontend shall reflect the updated `completed` state immediately after a successful toggle response, without requiring a full page reload.

---

### Requirement 7: Task Deletion

**Objective:** As an authenticated user, I want to permanently delete tasks I no longer need, so that my task list remains organized.

#### Acceptance Criteria

1. When an authenticated user requests deletion of a task they own, the Todo App shall permanently remove the task and return a success confirmation.
2. If a user attempts to delete a task that does not belong to them, the Todo App shall reject the request with an authorization error and shall not delete any data.
3. If the requested task identifier does not exist, the Todo App shall return a not-found error.
4. When a task is successfully deleted, the Angular Frontend shall remove it from the displayed list without requiring a page reload.

---

### Requirement 8: Protected Routes and Session Persistence

**Objective:** As an authenticated user, I want my session to persist across page refreshes so that I do not have to log in repeatedly, and I want unauthenticated visitors to be redirected to the login page when they attempt to access protected areas.

#### Acceptance Criteria

1. While a valid authentication token is stored on the client, the Angular Frontend shall automatically attach the token to every API request requiring authentication.
2. When an unauthenticated visitor attempts to navigate to a protected route, the Angular Frontend shall redirect the visitor to the login page.
3. When an authenticated user's token expires, the Angular Frontend shall redirect the user to the login page and display a session-expiry notification.
4. The Angular Frontend shall store the authentication token in a way that survives a browser page refresh for the duration of the token's validity.
5. If the Todo App returns a 401 Unauthorized response, the Angular Frontend shall clear the stored token and redirect the user to the login page.

---

### Requirement 9: API Design and Project Structure

**Objective:** As a developer, I want the project to be cleanly separated into `backend/` and `frontend/` directories with well-defined API contracts, so that each layer can be developed and deployed independently.

#### Acceptance Criteria

1. The Todo App shall organize all FastAPI source code exclusively within the `backend/` directory.
2. The Todo App shall organize all Angular source code exclusively within the `frontend/` directory.
3. The FastAPI Backend shall expose a RESTful API with versioned endpoints (e.g., `/api/v1/`) for all authentication and task operations.
4. The FastAPI Backend shall provide an OpenAPI (Swagger) specification document automatically generated from the route definitions.
5. The FastAPI Backend shall include CORS configuration that allows requests from the Angular Frontend's configured origin.
6. The Todo App shall require no source files to be placed outside the `backend/` or `frontend/` directories, aside from root-level configuration and documentation files.

### Requirement 10: Responsive and Clean UI

**Objective:** As a user, I want the frontend to be visually clean and work well on any screen size, so that I can use the application comfortably on desktop, tablet, or mobile.

#### Acceptance Criteria

1. The Angular Frontend shall use a responsive layout that adapts to screen widths from 320px (mobile) through desktop sizes without horizontal scrolling.
2. The Angular Frontend shall apply consistent spacing, typography, and color across all pages (login, registration, task list).
3. The Angular Frontend shall provide clear visual distinction between pending and completed tasks (e.g., strikethrough, muted color, or icon).
4. Interactive elements (buttons, inputs, checkboxes) shall have sufficient touch target sizes and hover/focus states for accessibility.
5. The Angular Frontend shall display inline validation errors adjacent to the relevant form field, in a readable and unobtrusive style.

---

### Requirement 12: Database Migrations

**Objective:** As a developer, I want all database schema changes managed through Alembic migrations, so that schema evolution is versioned and reproducible.

#### Acceptance Criteria

1. The FastAPI Backend shall use Alembic to manage all SQLite database schema changes, with migration scripts stored in `backend/alembic/versions/`.
2. The initial Alembic migration shall create the `tasks` table with columns `id` (UUID, primary key), `userId` (UUID, not null), `title` (VARCHAR, not null), and `completed` (BOOLEAN, not null, default false).
3. The FastAPI Backend shall run pending Alembic migrations automatically on application startup before accepting requests.
4. When a developer runs `alembic upgrade head` inside the `backend/` directory, the Todo App shall apply all pending migrations to the SQLite database in order.
5. Each Alembic migration file shall be reversible — the Todo App shall support `alembic downgrade` for every migration that has a corresponding upgrade.
