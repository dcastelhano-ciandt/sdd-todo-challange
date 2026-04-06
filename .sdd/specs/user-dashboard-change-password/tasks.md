# Implementation Plan

- [x] 1. (P) Add the `update_password` persistence method to the User Repository
  - Add a method that accepts a user ID and a new bcrypt-hashed password string, fetches the matching user record, updates the `hashed_password` column, commits the transaction, and returns the updated user entity
  - Raise a `NotFoundError` if no user is found for the given ID
  - No schema migration is required; only the existing `users.hashed_password` column is written
  - Can be implemented and tested in parallel with task 4 — both touch completely separate files
  - _Requirements: 4.1_

- [x] 2. Extend the Auth Service with `change_password` and `get_user_email`
  - Add `change_password(user_id, jti, expires_at, current_password, new_password)` that: (1) loads the user via the repository, (2) verifies the current password using constant-time bcrypt comparison, (3) hashes the new password, (4) persists it via `update_password` (task 1), (5) blacklists the old JWT by calling the existing `logout` method, and (6) issues and returns a new `TokenResponse`
  - Raise `AuthenticationError` with a clear message when the current password is incorrect; this propagates to HTTP 401 via the existing global exception handler
  - Perform the `update_password` and token blacklist writes within a single transaction so that a DB failure on the blacklist step rolls back the password change as well (no partial state)
  - Add `get_user_email(user_id)` that loads the user and returns the email string; raise `NotFoundError` if not found
  - Depends on task 1 (`update_password`) being implemented first
  - _Requirements: 4.1, 4.2, 5.4, 1.2_

- [x] 3. Add the `PATCH /api/v1/auth/change-password` and `GET /api/v1/auth/me` endpoints to the Auth Router
  - Define the `ChangePasswordRequest` Pydantic model with `current_password` and `new_password` (min length 8 enforced via field validator); define `UserProfileResponse` with `email`
  - Implement `PATCH /api/v1/auth/change-password`: require a valid Bearer token, extract the raw token to obtain the JTI and expiry for blacklisting, delegate to `AuthService.change_password`, and return a `TokenResponse` on success
  - Implement `GET /api/v1/auth/me`: require a valid Bearer token, delegate to `AuthService.get_user_email`, and return a `UserProfileResponse`
  - Map `AuthenticationError` → 401 and `ValidationError` → 422 via the existing global exception handlers (no new error handling code required)
  - Depends on task 2 (`change_password` and `get_user_email`) being implemented first
  - _Requirements: 4.1, 4.2, 3.3, 1.2_

- [x] 4. (P) Extend the frontend Auth API Service with `changePassword` and `getProfile`
  - Add `changePassword(currentPassword, newPassword)` that issues a `PATCH` request to `/api/v1/auth/change-password` with the two password values and returns an `Observable` resolving to the new access token string
  - Add `getProfile()` that issues a `GET` request to `/api/v1/auth/me` and returns an `Observable<UserProfile>` containing the email field
  - Follow the existing service patterns: use `inject(HttpClient)`, pipe through `map`, and do not handle errors inside the service (error handling is delegated to the component)
  - The `authInterceptor` automatically attaches the Bearer token to both requests; no additional auth wiring is needed
  - Can be implemented in parallel with task 1 — this file is fully independent of the backend repository layer
  - _Requirements: 4.1, 1.2_

- [ ] 5. Implement the Dashboard Component
- [x] 5.1 Build the component skeleton, read-only email display, and profile loading
  - Create a new standalone Angular component for the dashboard page
  - On initialization, call `getProfile()` from the Auth API service and display the returned email in a visually disabled text input that prevents any editing
  - Handle a profile-loading failure gracefully (display a generic error message rather than leaving the email field blank)
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 5.2 Implement the change-password reactive form with client-side validation
  - Build a `FormGroup` with three controls: current password, new password, and confirm new password; all must be `type="password"` masked inputs
  - Apply `Validators.required` to all three controls and `Validators.minLength(8)` to the new password and confirm fields
  - Implement a synchronous cross-field validator at the group level that compares the new password and confirm new password values and sets a `passwordsMismatch` error on the group when they differ
  - Display per-field inline error messages: required field errors for each blank field, a minimum-length message for the new password, and a mismatch message beneath the confirm field
  - Keep the submit button disabled whenever the form is invalid or a submission is in progress
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_

- [x] 5.3 Implement form submission, loading state, and result handling
  - On submit, set a `submitting` flag to `true` and disable the submit button immediately to prevent duplicate submissions
  - Call `changePassword` from the Auth API service with the current and new password values
  - On success: store the new access token via `AuthStateService.setToken()`, display a success confirmation message, reset the form to clear all three password fields, and set `submitting` back to `false`
  - On a 401 response indicating an incorrect current password, display a specific error message on the current password field and set `submitting` back to `false`
  - On any other server error (4xx/5xx), display a generic error message without exposing raw server details and set `submitting` back to `false`
  - Never log or persist any password field value; clear the `FormGroup` reference on reset
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2_

- [x] 6. Register the dashboard route and add the navigation link
  - Register a lazy-loaded `/dashboard` route in `app.routes.ts` protected by `authGuard`; unauthenticated navigation attempts redirect to `/login` via the existing guard
  - Add a "Dashboard" or "Account" navigation link in the task list page header alongside the existing Logout button so authenticated users can reach the dashboard
  - Verify that the existing `authInterceptor` handles session expiry on the dashboard page (any 401 on a non-auth endpoint triggers `clearSession()` and redirects to `/login` with a session-expiry indicator)
  - Depends on task 5 (component must exist before the route can reference it)
  - _Requirements: 1.1, 1.3, 2.4, 5.1, 5.3_

- [ ] 7. Write backend tests for the new password-change functionality
- [x] 7.1 (P) Write unit tests for `AuthService.change_password` and `UserRepository.update_password`
  - Test `change_password` with a correct current password: verify that `update_password` is called with the new hash, the old JTI is blacklisted, and a new `TokenResponse` is returned
  - Test `change_password` with an incorrect current password: verify that `AuthenticationError` is raised and that `update_password` is never called
  - Test `update_password` directly against an in-memory SQLite session: verify the `hashed_password` column is updated and the returned entity reflects the new value
  - Test `get_user_email` with a known user ID (returns email) and an unknown user ID (raises `NotFoundError`)
  - _Requirements: 4.1, 4.2, 1.2_

- [x] 7.2 Write backend integration tests for the new endpoints
  - Test `PATCH /api/v1/auth/change-password` with a valid Bearer token and correct current password: expect HTTP 200, a new token in the response, the updated `hashed_password` in the database, and the old JTI present in `token_blacklist`
  - Test the same endpoint with a correct token but wrong current password: expect HTTP 401 and the `hashed_password` unchanged in the database
  - Test the same endpoint without a Bearer token: expect HTTP 401
  - Test that presenting the old token after a successful password change returns HTTP 401 (token blacklisted)
  - Test `GET /api/v1/auth/me` with a valid token: expect HTTP 200 and the correct email in the response body
  - _Requirements: 4.1, 4.2, 4.3, 5.4, 1.2_

- [ ] 8. Write frontend tests for the Dashboard Component and Auth API Service
- [x] 8.1 (P) Write Angular unit tests for the change-password form and Auth API Service extension
  - Test the `passwordsMatchValidator`: returns no error when both passwords match; sets `passwordsMismatch` on the group when they differ
  - Test form validation states: submit button is disabled when any field is empty, when passwords are shorter than 8 characters, and when the passwords mismatch; enabled only when all conditions pass
  - Test `AuthApiService.changePassword` and `AuthApiService.getProfile` with an `HttpClientTestingModule` mock: verify the correct HTTP verbs, URLs, and payload shapes
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1_

- [x] 8.2 Write E2E tests for the dashboard user journey
  - Navigate to `/dashboard` without authentication: verify redirect to `/login`
  - Navigate to `/dashboard` as an authenticated user: verify the email field is populated, is read-only, and cannot be edited
  - Submit the change-password form with all fields empty: verify per-field required error messages appear
  - Submit with mismatched new password and confirm password: verify the mismatch error is shown and no HTTP request is made
  - Submit with a correct current password and a valid new password: verify the success message is displayed and all password fields are cleared
  - Submit with an incorrect current password: verify the server error message is shown and the fields retain their values
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.2, 4.3, 4.4_
