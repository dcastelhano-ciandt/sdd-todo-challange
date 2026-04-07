# Implementation Plan

---

## Search Feature — Implementation Tasks

---

- [x] 1. Extend the task repository to support case-insensitive title search
- [x] 1.1 (P) Write unit tests for the repository search behavior before implementing it
  - Verify that passing a keyword to the listing method returns only tasks whose titles contain the keyword, regardless of letter casing
  - Verify that passing `None` as the keyword returns all tasks without any title filter (backward-compatible behavior)
  - Verify that passing both a status and a keyword applies both filters simultaneously and returns only the tasks that satisfy both conditions
  - Verify that results are ordered by creation date descending when a keyword filter is active
  - Use the existing in-memory SQLite fixture pattern from the repository test suite
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 1.2 (P) Add an optional keyword parameter to the repository listing method and apply a case-insensitive LIKE filter
  - Accept an optional keyword argument alongside the existing status argument
  - When the keyword is provided, chain a filter that lowercases both the stored title and the search keyword and matches any substring
  - When the keyword is absent, leave the existing query unchanged so all existing behavior is preserved
  - Preserve the descending creation-date ordering regardless of whether a keyword filter is applied
  - Rely on SQLAlchemy parameterized expressions to avoid SQL injection
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 1.2, 1.4, 1.5_

---

- [x] 2. Extend the task service to normalize and propagate the search keyword
- [x] 2.1 (P) Write unit tests for the service keyword-normalization behavior before implementing it
  - Verify that a whitespace-only keyword is converted to `None` before being passed to the repository (no title filter applied)
  - Verify that a non-empty keyword after stripping is forwarded to the repository unchanged
  - Verify that calling the method without a keyword passes `None` to the repository (backward-compatible)
  - Mock the repository to isolate service-layer logic
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2.2 (P) Add an optional keyword parameter to the service listing method and normalize whitespace
  - Accept an optional keyword argument in the listing method signature
  - Strip whitespace from the keyword; treat an empty or whitespace-only result as no filter
  - Pass the cleaned keyword to the repository when it is non-empty, otherwise pass `None`
  - Leave all other service behaviors (status translation, user scoping) unchanged
  - _Requirements: 3.1, 3.2, 3.3_

---

- [x] 3. Expose the search keyword through the tasks API endpoint
- [x] 3.1 Write unit tests for the router keyword parameter before implementing it
  - Verify the endpoint accepts a `q` query parameter and forwards it to the service
  - Verify omitting `q` preserves the existing response without title filtering
  - Verify that an authenticated request with both `q` and `status` applies both filters and restricts results to the requesting user
  - Use the FastAPI `TestClient` pattern consistent with existing router tests
  - _Requirements: 1.1, 1.3, 1.6_

- [x] 3.2 Add the `q` query parameter to the list-tasks endpoint and wire it to the service
  - Declare `q` as an optional `Query` parameter with a `None` default alongside the existing `status` parameter
  - Pass the raw value of `q` verbatim to the service (whitespace normalization is the service's responsibility)
  - Leave user scoping and all other endpoint behavior unchanged
  - _Requirements: 1.1, 1.3, 1.4, 1.6_

---

- [x] 4. Extend the frontend HTTP service to include the search keyword in API requests
- [x] 4.1 (P) Write unit tests for the API service keyword parameter before implementing it
  - Verify that calling the listing method with a keyword appends `?q=<keyword>` to the request URL
  - Verify that calling with both a status and a keyword appends both parameters in a single request
  - Verify that passing an empty string does not append a `q` parameter to the URL
  - Verify that calling without a keyword produces the same URL as before (backward-compatible)
  - Follow the existing `HttpTestingController` pattern from the API service spec file
  - _Requirements: 5.4_

- [x] 4.2 (P) Add an optional keyword parameter to the API service listing method and conditionally append it to the query string
  - Extend the `listTasks` method signature with an optional `q` string parameter
  - Append `q` to `HttpParams` only when the value is a non-empty string, replicating the existing truthy-check pattern used for `status`
  - Leave all other HTTP construction logic unchanged
  - _Requirements: 5.4, 7.1_

---

- [x] 5. Extend the frontend state service to accept and forward the search keyword
- [x] 5.1 (P) Write unit tests for the state service keyword forwarding before implementing it
  - Verify that calling `loadTasks` with a keyword passes both the keyword and the current filter value to the API service
  - Verify that calling `loadTasks` without a keyword passes `undefined` as the keyword while still reading the current filter (backward-compatible)
  - Verify that the `filter` signal value is read at call time so that a filter change followed by `loadTasks` picks up the new filter without needing the keyword to change
  - Verify that passing a keyword does not reset the filter signal and that changing the filter does not clear any keyword passed in the next `loadTasks` call
  - Follow the existing `HttpTestingController` pattern from the state service spec file
  - _Requirements: 5.3, 7.1, 7.3_

- [x] 5.2 (P) Update the state service to accept a keyword in `loadTasks` and pass it alongside the status to the API service
  - Change the `loadTasks` method signature to accept an optional `q` string parameter
  - Derive the `status` argument from the `filter` signal at call time (replace the hardcoded `undefined` with the signal value when filter is not `'all'`)
  - Pass both `status` and `q` to `TaskApiService.listTasks`
  - Remove the client-side filtering in the `tasks` computed signal so that the API result is used directly as the authoritative task list (the server now does the filtering)
  - Leave the `_loading` signal management, error handling, and all other state mutations unchanged
  - _Requirements: 5.3, 7.1, 7.2, 7.3_

---

- [x] 6. Add the search input, debounce logic, and updated empty state to the task list component
- [x] 6.1 Write unit tests for the search input rendering and clear behavior before implementing it
  - Verify that the search input element is rendered above the filter buttons in the component template
  - Verify that the input has a leading search icon and a trailing clear icon
  - Verify that the clear icon sets the search term to empty and immediately triggers a task reload without any debounce delay
  - Verify that the loading indicator is shown and the empty state is suppressed while a search is in progress
  - Verify that when the task list is empty and a search term is active, the message "No results for '[term]'" is displayed
  - Verify that when the task list is empty and no search term is active, the default empty state message is displayed
  - Follow the mocked `TaskStateService` pattern from the existing component spec file
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3, 6.4_

- [x] 6.2 Implement the search input markup in the component template
  - Insert a search bar wrapper `div` between the page header and the filter controls, matching the layout from the UI reference
  - Add a leading `search` Material Symbols icon inside the wrapper
  - Add a text input with `data-testid="search-input"`, bound two-way to the `searchTerm` component field, with placeholder text that communicates its purpose
  - Add a trailing close icon with `data-testid="clear-search"` that calls `clearSearch()` on click
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 6.3 Implement the search term state, debounce handler, and clear action in the component class
  - Add a `searchTerm` string field initialized to empty string as the owner of the search state
  - Add a private `debounceTimer` field to manage the 300 ms debounce lifecycle
  - Implement `onSearchInput(value)` to clear any pending timer and start a new 300 ms timer that calls `loadTasks` with the current search term on expiry
  - Bind the `(input)` event on the search input to `onSearchInput($event.target.value)`
  - Implement `clearSearch()` to reset `searchTerm` to empty and immediately call `loadTasks` without debounce
  - Add `ngOnDestroy` to cancel any pending timer when the component is destroyed
  - Update the initial `ngOnInit` call to `loadTasks()` without any keyword argument
  - _Requirements: 4.5, 4.6, 5.1, 5.2, 5.5_

- [x] 6.4 Update the filter button handlers to re-execute `loadTasks` with the current search term after changing the filter
  - Change each filter button's click binding from a single `filter.set(value)` call to a two-step sequence: set the filter signal then immediately call `loadTasks(searchTerm)`
  - This ensures that a status change while a search term is active issues a new API request with both parameters and does not reset the search term
  - _Requirements: 7.2, 7.4_

- [x] 6.5 Replace the empty state template block with a conditional that distinguishes search results from no tasks
  - When `searchTerm` is non-empty and the returned task list is empty, display "No results for '[searchTerm]'"
  - When no search term is active and the task list is empty, display the default message "No tasks yet. Create your first task to get started."
  - Ensure the empty state block remains suppressed while the loading signal is true
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

---

- [x] 7. Write backend integration tests that verify the search endpoint end-to-end
- [x] 7.1 Add integration tests for the search query parameter to the existing integration test suite
  - Test that `GET /api/v1/tasks?q=<keyword>` returns only tasks owned by the authenticated user whose titles contain the keyword, case-insensitively
  - Test that `GET /api/v1/tasks?status=pending&q=<keyword>` returns only pending tasks matching the keyword
  - Test that `GET /api/v1/tasks?q=<keyword>` returns `{"tasks": []}` with HTTP 200 when no tasks match
  - Test that `GET /api/v1/tasks?q=<UPPER>` and `?q=<lower>` return the same results, confirming case-insensitive matching
  - Test that `GET /api/v1/tasks?q=` (empty string) returns all tasks for the user, identical to calling without any `q` parameter
  - Follow the `TestClient` and shared in-memory database fixture pattern used in the existing integration test file
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

---

- [x] 8. Write end-to-end tests that verify the full search user journey
- [x] 8.1 Add E2E tests covering the search interaction flows
  - Test that typing a keyword into the search input causes the task list to update after the debounce delay, showing only matching tasks
  - Test that clicking the clear icon empties the search input and reloads the full task list
  - Test that searching for a keyword with no matching tasks displays the "No results for '...'" message and hides the default empty state
  - Test that typing a keyword while a status filter is active sends both parameters in the request and the result set respects both constraints
  - Test that changing the status filter while a search term is active keeps the search term in the new request and does not reset it
  - _Requirements: 4.4, 4.5, 5.1, 5.5, 6.1, 6.3, 7.2, 7.3, 7.4_
