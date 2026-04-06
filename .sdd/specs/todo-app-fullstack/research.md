# Research & Design Decisions

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

---

## Summary

- **Feature**: `todo-app-fullstack`
- **Discovery Scope**: New Feature (greenfield full-stack application)
- **Key Findings**:
  - FastAPI with SQLAlchemy (sync) and Alembic is the idiomatic Python stack for this scope; async SQLAlchemy adds complexity without benefit at this scale.
  - JWT access tokens with short TTL (30 min) combined with client-side localStorage persistence and an HTTP interceptor is the standard Angular auth pattern. Server-side token blacklisting for logout is the simplest compliant approach given SQLite availability.
  - Angular standalone components (Angular 17+) with a Feature-Module-like organisation (auth feature, tasks feature, shared) align with current Angular best practices and avoid NgModule boilerplate.

---

## Research Log

### JWT Authentication in FastAPI

- **Context**: Requirements 1 and 2 mandate JWT issuance on registration/login and token expiry enforcement.
- **Sources Consulted**: FastAPI official security docs; python-jose GitHub; passlib docs.
- **Findings**:
  - `python-jose[cryptography]` is the recommended JWT library for FastAPI (`jose.jwt.encode/decode`).
  - `passlib[bcrypt]` provides `CryptContext` for password hashing with constant-time verification.
  - FastAPI's `OAuth2PasswordBearer` dependency extracts the Bearer token from `Authorization` headers and feeds it to a `get_current_user` dependency.
  - Access token payload should contain `sub` (user ID as UUID string), `exp`, and `iat` claims.
  - A 30-minute access token TTL is the standard minimum; no refresh token is required by the requirements.
- **Implications**:
  - `AuthService` (backend) owns hashing and token operations. `get_current_user` dependency is injected into all protected routes.
  - Token expiry rejection (requirement 2.3) is handled by `jose.jwt.decode` raising `JWTError` on expired tokens.

### Token Logout / Invalidation

- **Context**: Requirement 2.5 requires token invalidation on logout so the previously issued token can no longer be used.
- **Sources Consulted**: OWASP JWT cheat sheet; FastAPI community patterns.
- **Findings**:
  - Stateless JWTs cannot be truly invalidated without server-side state.
  - Options: (a) token blacklist in DB/cache, (b) very short TTL with no logout endpoint, (c) user-specific token generation counter.
  - For this scope (SQLite, single-process), a `token_blacklist` table with the JWT `jti` claim and expiry is the simplest persistent approach.
- **Implications**:
  - `AuthService` writes `jti` to `token_blacklist` on logout. `get_current_user` dependency checks the blacklist on every request.
  - `jti` (UUID) is added to every token payload at issuance.

### Alembic with SQLAlchemy

- **Context**: Requirement 10 mandates Alembic migrations run on startup.
- **Sources Consulted**: Alembic official docs; SQLAlchemy 2.x migration guide.
- **Findings**:
  - `alembic upgrade head` called programmatically via `alembic.command.upgrade(alembic_cfg, "head")` in the FastAPI lifespan startup hook satisfies requirement 10.3.
  - Initial migration must create `users` and `tasks` tables. Even though `users` is not listed in the requirements data model, it is implied by the authentication requirements.
  - UUID primary keys are stored as `VARCHAR(36)` in SQLite (no native UUID type).
- **Implications**:
  - Two tables in the initial migration: `users` (id, email, hashed_password) and `tasks` (id, userId, title, completed, created_at).
  - `created_at` column is needed for default ordering (requirement 4.1) but not listed in the data model — it is an implementation necessity.

### Angular Auth Pattern

- **Context**: Requirements 8.1–8.5 specify token auto-attachment, route guards, 401 handling, and localStorage persistence.
- **Sources Consulted**: Angular official docs (HttpClient, Guards, Interceptors); Angular 17 standalone API.
- **Findings**:
  - Angular 17 uses functional `HttpInterceptorFn` (no class-based interceptor needed) registered in `provideHttpClient(withInterceptors([...]))`.
  - `CanActivateFn` (functional guard) checks token presence and expiry before route activation.
  - `localStorage` persists across page refreshes; token is set on login/register and cleared on logout or 401.
  - The interceptor reads the token from a `AuthStateService` (singleton) which reads from localStorage on init.
- **Implications**:
  - `AuthInterceptor` (functional) attaches `Authorization: Bearer <token>` to every non-auth request.
  - `AuthGuard` redirects to `/login` if no valid token is present.
  - `AuthStateService` is the single source of truth for token state on the frontend.

### Angular Task State Management

- **Context**: Requirements 4.4 (loading indicator), 6.4 (immediate toggle update), 7.4 (immediate deletion) imply reactive UI state.
- **Findings**:
  - Angular Signals (Angular 17+) or RxJS BehaviorSubject in a `TaskStateService` are both viable. Signals are the modern preferred approach.
  - Optimistic UI update (toggle/delete) improves perceived performance: update state immediately, rollback on API error.
- **Implications**:
  - `TaskStateService` holds tasks as a `Signal<Task[]>`, exposes methods for CRUD operations that call the API and update state.

---

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Layered (Router → Service → Repository) | Backend split into HTTP layer, business logic, and data access | Clear separation, testable services, standard FastAPI idiom | Slight verbosity for simple CRUD | Selected for backend |
| Active Record (SQLAlchemy models as logic) | Models contain business methods | Less boilerplate | Couples business logic to ORM, harder to test | Rejected |
| Feature modules (Angular) | Frontend grouped by feature: auth, tasks, shared | Lazy-loadable, bounded, parallel development | Slight setup overhead | Selected for frontend |
| Monolithic Angular service | Single service handles auth + tasks | Simpler initial setup | Poor separation, grows unmaintainable | Rejected |

---

## Design Decisions

### Decision: Synchronous SQLAlchemy over Async

- **Context**: SQLAlchemy supports both sync and async sessions. Async requires `aiosqlite` driver.
- **Alternatives Considered**:
  1. Async SQLAlchemy + aiosqlite — full async pipeline
  2. Sync SQLAlchemy + `run_in_executor` in FastAPI — sync ORM with async endpoints
  3. Sync SQLAlchemy with sync FastAPI endpoints — simplest
- **Selected Approach**: Sync SQLAlchemy with sync route handlers (FastAPI runs sync handlers in thread pool automatically).
- **Rationale**: SQLite is a file-based DB with no true async benefit. Sync SQLAlchemy is simpler and better documented for Alembic autogenerate.
- **Trade-offs**: Not suitable for high-concurrency production use; acceptable for this scope.
- **Follow-up**: If PostgreSQL is adopted later, migrate to async SQLAlchemy.

### Decision: Token Blacklist for Logout

- **Context**: Stateless JWT cannot be invalidated without server state.
- **Alternatives Considered**:
  1. Ignore logout (accept until token expiry) — fails requirement 2.5
  2. Token blacklist in SQLite — persistent, simple
  3. Short TTL + no logout — fails requirement 2.5 exactly
- **Selected Approach**: `token_blacklist` table storing `jti` and `expires_at`; checked on every authenticated request.
- **Rationale**: Simple to implement with existing SQLite + SQLAlchemy infrastructure. Cleanup of expired entries can be done lazily on read.
- **Trade-offs**: Adds one DB read per authenticated request. Acceptable at this scale.

### Decision: Angular Signals for Task State

- **Context**: Tasks need reactive updates without full page reload.
- **Alternatives Considered**:
  1. RxJS BehaviorSubject — established pattern, more complex
  2. Angular Signals — modern, simpler, built-in to Angular 17+
  3. NgRx Store — full state management, overkill for this scope
- **Selected Approach**: Angular Signals in `TaskStateService`.
- **Rationale**: Signals are the Angular 17+ recommended pattern for component-level reactive state. Reduces RxJS boilerplate.
- **Trade-offs**: Less familiar to developers trained on RxJS-only patterns.

### Decision: users Table Not in Requirements Data Model

- **Context**: Requirements define only the `tasks` table schema. Authentication requirements imply a `users` table.
- **Selected Approach**: Add `users` table (id UUID PK, email VARCHAR unique, hashed_password VARCHAR) in the initial migration alongside `tasks`.
- **Rationale**: Cannot implement requirements 1–2 without user persistence. The requirements data model section covers only task columns.

---

## Risks & Mitigations

- Token blacklist grows unbounded — Mitigation: delete expired entries lazily on every blacklist check, or add a periodic cleanup.
- SQLite concurrent write contention under load — Mitigation: acceptable for development; document that production deployment should use PostgreSQL.
- Angular localStorage XSS exposure — Mitigation: sanitize all user input; content-security-policy headers on backend responses; this is a development-scope application.
- Alembic autogenerate may miss server-side defaults — Mitigation: review generated migration SQL before applying; use explicit `server_default` in ORM models.
- CORS misconfiguration allowing broad origins — Mitigation: configure `CORSMiddleware` to allow only `http://localhost:4200` (Angular dev server) explicitly; document production origin requirement.

---

## References

- FastAPI Security documentation — https://fastapi.tiangolo.com/tutorial/security/
- python-jose GitHub — https://github.com/mpdavis/python-jose
- passlib documentation — https://passlib.readthedocs.io/
- Alembic documentation — https://alembic.sqlalchemy.org/
- SQLAlchemy 2.x documentation — https://docs.sqlalchemy.org/en/20/
- Angular HTTP Interceptors (functional) — https://angular.dev/guide/http/interceptors
- Angular Route Guards — https://angular.dev/guide/routing/common-router-tasks#preventing-unauthorized-access
- Angular Signals — https://angular.dev/guide/signals
- OWASP JWT Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
