# Implementation Plan

- [ ] 1. Set up backend project structure and configuration
- [x] 1.1 Scaffold the backend directory layout and install dependencies
  - Create the `backend/` directory tree matching the design: `app/routers/`, `app/services/`, `app/repositories/`, `app/models/`, `app/schemas/`, `app/core/`
  - Create `requirements.txt` with FastAPI, SQLAlchemy, Alembic, python-jose[cryptography], passlib[bcrypt], and email-validator
  - Create the core settings module that reads `SECRET_KEY`, token TTL, database URL, and allowed CORS origin from environment variables
  - Create the domain exceptions module with `AuthenticationError`, `ConflictError`, `NotFoundError`, `ForbiddenError`, and `ValidationError`
  - _Requirements: 9.1, 9.6_

- [x] 1.2 Bootstrap the FastAPI application with CORS, exception handlers, and lifespan
  - Create `app/main.py` with the FastAPI app instance and lifespan event hook
  - Register `CORSMiddleware` allowing only the configured Angular origin
  - Register global exception handlers that translate domain exceptions to the correct HTTP status codes (401, 403, 404, 409, 422)
  - Mount auth and task routers under `/api/v1/auth` and `/api/v1/tasks`
  - Confirm the OpenAPI spec is auto-generated and accessible at `/docs`
  - _Requirements: 9.3, 9.4, 9.5_

- [ ] 2. Configure Alembic and create the initial database migration
- [x] 2.1 Initialize Alembic and wire it to the SQLAlchemy base
  - Run `alembic init` inside `backend/` and configure `alembic.ini` and `env.py` to read the database URL from the application settings
  - _Requirements: 12.1, 12.4_

- [x] 2.2 Write the initial migration script for all three tables
  - Create `001_initial_schema.py` with `upgrade()` that creates `users` (id, email, hashed_password), `tasks` (id, userId FK→users ON DELETE CASCADE, title, completed, created_at), and `token_blacklist` (jti, expires_at)
  - Add indexes on `tasks(userId)` and `tasks(userId, completed)`; add index on `token_blacklist(expires_at)`
  - Implement `downgrade()` that drops the three tables in reverse dependency order
  - _Requirements: 12.2, 12.5_

- [ ] 2.3 Add the Alembic startup runner to the FastAPI lifespan
  - Call `alembic.command.upgrade(cfg, "head")` inside the FastAPI lifespan startup hook before accepting requests
  - _Requirements: 12.3_

- [ ] 3. Implement the backend data layer (SQLAlchemy models and repositories)
- [x] 3.1 (P) Define the SQLAlchemy ORM models
  - Create ORM models for `User`, `Task`, and `TokenBlacklist` matching the physical data model (VARCHAR(36) PKs, server defaults, FK cascade)
  - Expose a `get_db` FastAPI dependency that yields a `Session` and closes it after the request
  - _Requirements: 9.1_

- [x] 3.2 (P) Implement the User repository
  - Implement `find_by_email`, `find_by_id`, and `create` operations
  - Catch SQLAlchemy `IntegrityError` on duplicate email and re-raise as `ConflictError`
  - _Requirements: 1.1, 1.2, 1.4, 2.1, 2.2_

- [x] 3.3 (P) Implement the Task repository
  - Implement `create`, `list_by_user`, `get_by_id`, `update`, and `delete` operations
  - `list_by_user` applies `WHERE userId = :user_id`, optional `completed` filter, and `ORDER BY created_at DESC`
  - _Requirements: 3.1, 3.3, 4.1, 4.2, 4.3, 5.1, 6.1, 6.2, 7.1_

- [ ] 4. Implement the Auth service and authentication dependency
- [x] 4.1 Implement password hashing and JWT token operations in AuthService
  - Implement `hash_password` using bcrypt via passlib `CryptContext`; implement `verify_password` with constant-time comparison
  - Implement `create_access_token` that embeds `sub` (user UUID), `exp`, `iat`, and `jti` (UUID) claims and signs with `SECRET_KEY`
  - Implement `decode_token` that verifies signature and expiry, checks `token_blacklist` by `jti`, and raises `AuthenticationError` on failure
  - _Requirements: 1.4, 2.1, 2.3, 2.5_

- [x] 4.2 Implement registration and login business logic in AuthService
  - Implement `register`: validate that the email is not already taken, hash the password, persist the user via `UserRepository`, and return a `TokenResponse`
  - Implement `login`: look up the user by email, verify the password hash; on any mismatch raise a generic `AuthenticationError` (never disclose email vs. password)
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 2.1, 2.2_

- [x] 4.3 Implement the logout operation and token blacklist management
  - Implement `logout` in `AuthService`: insert `(jti, expires_at)` into `token_blacklist`; prune expired entries lazily in the same call
  - _Requirements: 2.5_

- [x] 4.4 Implement the `get_current_user` FastAPI dependency
  - Extract the Bearer token via `OAuth2PasswordBearer`; call `AuthService.decode_token`; return a `UserContext` with `user_id` and `jti`
  - Raise `HTTPException(401)` for any invalid, expired, or blacklisted token
  - _Requirements: 2.1, 2.3, 2.4, 2.5_

- [ ] 5. Implement the Task service
- [x] 5.1 (P) Implement task creation and listing in TaskService
  - Implement `create_task`: generate a UUID for the new task, set `completed=False`, validate that the title is non-empty, delegate to `TaskRepository.create`
  - Implement `list_tasks`: delegate to `TaskRepository.list_by_user` with optional status filter; return tasks ordered by creation date descending
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_

- [x] 5.2 (P) Implement task mutation operations in TaskService
  - Implement `update_task`: fetch by ID, verify ownership (`task.userId == user_id`), validate non-empty title, persist and return updated task
  - Implement `toggle_completion`: fetch by ID, verify ownership, flip the `completed` boolean, persist and return updated task
  - Implement `delete_task`: fetch by ID, verify ownership, call `TaskRepository.delete`; raise `NotFoundError` when task ID is missing
  - Ownership check must always precede any mutation — never update then check
  - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3_

- [ ] 6. Implement the backend HTTP routers
- [x] 6.1 (P) Implement the Auth router with Pydantic request/response schemas
  - Create Pydantic models: `RegisterRequest` (EmailStr, password min_length=8), `LoginRequest`, `TokenResponse`, `MessageResponse`
  - Implement `POST /api/v1/auth/register` → 201 `TokenResponse`; 409 on duplicate email; 422 on validation failure
  - Implement `POST /api/v1/auth/login` → 200 `TokenResponse`; 401 on any invalid credentials
  - Implement `POST /api/v1/auth/logout` (requires Bearer token) → 200 `MessageResponse`; calls `AuthService.logout` with `jti` from the token
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 2.1, 2.2, 2.5, 9.3_

- [x] 6.2 (P) Implement the Task router with Pydantic request/response schemas
  - Create Pydantic models: `CreateTaskRequest` (title min_length=1), `UpdateTaskRequest` (title min_length=1), `TaskResponse`, `TaskListResponse`
  - Implement `POST /api/v1/tasks` → 201 `TaskResponse`; all endpoints inject `get_current_user` so `user_id` always comes from the validated JWT
  - Implement `GET /api/v1/tasks?status=pending|completed` → 200 `TaskListResponse`
  - Implement `PUT /api/v1/tasks/{task_id}` → 200 `TaskResponse`; 403/404/422 on error conditions
  - Implement `PATCH /api/v1/tasks/{task_id}/toggle` → 200 `TaskResponse`; 403/404 on error conditions
  - Implement `DELETE /api/v1/tasks/{task_id}` → 200 `MessageResponse`; 403/404 on error conditions
  - Validate UUID format for `task_id` at the router level
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3, 9.3_

- [ ] 7. Set up the Angular frontend project
- [x] 7.1 Scaffold the Angular application with standalone components and routing
  - Create the Angular 17+ project inside `frontend/` using the standalone component API (no NgModules)
  - Configure `app.config.ts` with `provideRouter`, `provideHttpClient(withInterceptors([authInterceptor]))`, and the auth interceptor registration
  - Define route table in `app.routes.ts` with `/login`, `/register`, and `/tasks` (guarded by `authGuard`)
  - Create the TypeScript shared models: `Task`, `TokenResponse`, `CreateTaskRequest`, `UpdateTaskRequest`, `TaskStatus`, `ApiError`, `ValidationErrorDetail`
  - _Requirements: 9.2, 9.6_

- [ ] 8. Implement frontend authentication state and HTTP infrastructure
- [x] 8.1 (P) Implement AuthStateService with localStorage persistence
  - On service initialization, read `auth_token` from localStorage and initialize a writable Signal
  - Expose `token: Signal<string | null>`, `isAuthenticated: Signal<boolean>`, `setToken(token)`, `clearSession()`, and `getToken()`
  - `setToken` writes to localStorage; `clearSession` removes the key and resets the Signal
  - _Requirements: 8.1, 8.4, 8.5_

- [x] 8.2 (P) Implement the functional AuthInterceptor
  - Read the token from `AuthStateService.getToken()` on every outgoing request
  - Clone the request and attach `Authorization: Bearer <token>` when a token is present
  - Intercept 401 responses: call `AuthStateService.clearSession()` and redirect to `/login`
  - Register via `provideHttpClient(withInterceptors([authInterceptor]))` in `app.config.ts`
  - _Requirements: 8.1, 8.5_

- [x] 8.3 (P) Implement the functional AuthGuard
  - Check `AuthStateService.isAuthenticated` signal; allow navigation if true
  - Redirect to `/login` if false; pass an optional session-expiry query param when redirected by the interceptor
  - Apply the guard to the `/tasks` route in `app.routes.ts`
  - _Requirements: 8.2, 8.3_

- [ ] 9. Implement frontend authentication feature (login and registration UI)
- [x] 9.1 (P) Implement the auth API service
  - Create `auth-api.service.ts` with `register(email, password)` and `login(email, password)` methods that POST to `/api/v1/auth/register` and `/api/v1/auth/login` respectively
  - Both methods return the token from the response to the caller
  - _Requirements: 1.1, 2.1_

- [x] 9.2 (P) Implement the RegisterComponent
  - Build a reactive form with email and password fields; display inline field-level validation errors from both client-side validators and 422 API responses adjacent to the relevant field
  - On success, call `AuthStateService.setToken` and navigate to `/tasks`
  - On 409 (email in use), display the appropriate error message on the email field
  - _Requirements: 1.1, 1.2, 1.3, 10.2, 10.5_

- [x] 9.3 (P) Implement the LoginComponent
  - Build a reactive form with email and password fields; on 401 display a single generic error (do not indicate which field was wrong)
  - On success, call `AuthStateService.setToken` and navigate to `/tasks`
  - Display session-expiry notification when redirected from the guard with the expiry param
  - _Requirements: 2.1, 2.2, 8.3, 10.2, 10.5_

- [ ] 10. Implement frontend task state and task management UI
- [x] 10.1 Implement the task API service
  - Create `task-api.service.ts` with methods that call each task endpoint: `createTask`, `listTasks` (with optional status filter), `updateTask`, `toggleCompletion`, and `deleteTask`
  - _Requirements: 3.1, 4.1, 4.3, 5.1, 6.1, 7.1_

- [x] 10.2 Implement TaskStateService with Signal-based reactive state and optimistic updates
  - Hold tasks as `Signal<Task[]>` with `loading: Signal<boolean>` and `filter: WritableSignal<'all' | 'pending' | 'completed'>`
  - `loadTasks` sets loading to true, fetches from the API, updates the Signal, then clears loading
  - `toggleCompletion` and `deleteTask` apply an optimistic Signal update before the API call and restore the original snapshot on error (do not re-fetch from the API on rollback)
  - `createTask` and `updateTask` update the Signal after a successful API response
  - _Requirements: 4.4, 4.5, 6.4, 7.4_

- [x] 10.3 Implement TaskListComponent
  - On `ngOnInit`, call `TaskStateService.loadTasks()` to populate the list
  - Display a loading indicator while `loading` Signal is true
  - Display a descriptive empty-state message when the task list is empty
  - Render filter controls (all / pending / completed) that update `TaskStateService.filter`
  - Render a list of `TaskItemComponent` instances, one per task
  - _Requirements: 4.4, 4.5_

- [x] 10.4 Implement TaskItemComponent with inline edit, toggle, and delete
  - Display the task title with clear visual distinction for completed tasks (strikethrough and muted color)
  - Provide a completion toggle control that calls `TaskStateService.toggleCompletion`; the UI reflects the new state immediately after a successful response without a page reload
  - Provide an edit control for updating the title; on submit call `TaskStateService.updateTask`; validate that the title is non-empty before submission
  - Provide a delete control that calls `TaskStateService.deleteTask`; the task is removed from the list without a page reload
  - _Requirements: 5.1, 5.3, 6.4, 7.4_

- [ ] 11. Apply responsive and accessible styling across all views
- [x] 11.1 (P) Implement the responsive layout
  - Apply a fluid layout that works from 320 px mobile through desktop without horizontal scrolling
  - Use consistent spacing, typography, and color palette across `/login`, `/register`, and `/tasks` views
  - _Requirements: 10.1, 10.2_

- [x] 11.2 (P) Implement touch-friendly interactive elements and accessibility
  - Ensure all buttons, inputs, and checkboxes meet minimum touch target sizes and have visible hover/focus states
  - Display inline validation error messages adjacent to the relevant form field in an unobtrusive style
  - _Requirements: 10.3, 10.4, 10.5_

- [ ] 12. Write backend unit and integration tests
- [x] 12.1 (P) Write AuthService unit tests
  - Test `register` with valid input, duplicate email (expect ConflictError), and password below minimum length (expect ValidationError)
  - Test `login` with valid credentials, unknown email, and wrong password — last two must return identical errors
  - Test `decode_token` with a valid token, an expired token, and a blacklisted token
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.5_

- [x] 12.2 (P) Write TaskService unit tests
  - Test `create_task` with a valid title and with an empty title (expect ValidationError)
  - Test `toggle_completion` called by the task owner and by a different user (expect ForbiddenError)
  - Test `update_task` and `delete_task` with ownership violations (expect ForbiddenError) and missing task IDs (expect NotFoundError)
  - _Requirements: 3.1, 3.2, 5.2, 6.3, 7.2, 7.3_

- [x] 12.3 Write backend integration tests against an in-memory SQLite database
  - Test the full register → login → create task → list tasks flow through the HTTP API
  - Test cross-user task ownership: create a task as user A, attempt update and delete as user B — expect 403
  - Test token expiry: issue a token with zero TTL, make an authenticated request — expect 401
  - Test Alembic migration: run `upgrade head` against an empty database and verify all three tables exist with the correct columns
  - _Requirements: 1.1, 1.5, 2.1, 2.3, 3.1, 4.1, 5.2, 7.2, 12.1, 12.2, 12.3, 12.4_

- [x] 13. Write frontend unit and E2E tests
- [x] 13.1 (P) Write Angular unit tests for auth infrastructure
  - Test `AuthStateService`: `setToken` persists to localStorage, `clearSession` removes the key and resets the Signal
  - Test `AuthGuard`: returns `true` when a token is present, redirects to `/login` when absent
  - Test `AuthInterceptor`: attaches the `Authorization` header when a token is set, calls `clearSession` and redirects on a 401 response
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 13.2 (P) Write Angular unit tests for task state
  - Test `TaskStateService.toggleCompletion`: applies the optimistic update, and rolls back to the original snapshot on API error
  - Test `TaskStateService.loadTasks`: sets `loading` to true during the request and false after resolution
  - _Requirements: 4.4, 6.4_

- [x] 13.3 Write E2E tests for the full user journey
  - Full flow: register → login → create task → toggle completion → delete task
  - Unauthenticated access: navigate to `/tasks` without a token, verify redirect to `/login`
  - Session persistence: navigate to `/tasks` with a valid token in localStorage, verify tasks are still accessible after page reload
  - _Requirements: 8.2, 8.4_
