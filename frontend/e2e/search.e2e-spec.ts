import { test, expect, Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// Task 8.1 — Search feature E2E tests
// Requirements: 4.4, 4.5, 5.1, 5.5, 6.1, 6.3, 7.2, 7.3, 7.4
// ---------------------------------------------------------------------------

const BASE_URL = 'http://localhost:4200';
const API_BASE = '/api/v1';
const AUTH_TOKEN_KEY = 'auth_token';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function seedTokenInLocalStorage(page: Page, token: string): Promise<void> {
  await page.addInitScript(
    ({ key, value }: { key: string; value: string }) => {
      localStorage.setItem(key, value);
    },
    { key: AUTH_TOKEN_KEY, value: token },
  );
}

/**
 * Register a mock GET /api/v1/tasks handler that responds with the provided tasks
 * for ANY request URL matching the pattern (regardless of query parameters).
 * The handler is replaced on each call so tests can chain multiple mock responses.
 */
async function mockTaskListForUrl(
  page: Page,
  urlPattern: string,
  tasks: object[],
): Promise<void> {
  await page.route(urlPattern, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ tasks }),
      });
    } else {
      await route.continue();
    }
  });
}

// ---------------------------------------------------------------------------
// Test suite
// ---------------------------------------------------------------------------

test.describe('Search feature', () => {
  const GROCERY_TASK = {
    id: 'aaa00000-0000-0000-0000-000000000001',
    userId: 'user-uuid-1',
    title: 'Buy groceries',
    completed: false,
  };

  const REPORT_TASK = {
    id: 'bbb00000-0000-0000-0000-000000000002',
    userId: 'user-uuid-1',
    title: 'Write report',
    completed: false,
  };

  const PENDING_TASK = {
    id: 'ccc00000-0000-0000-0000-000000000003',
    userId: 'user-uuid-1',
    title: 'Buy bread (pending)',
    completed: false,
  };

  test('typing a keyword filters the task list after the debounce delay', async ({ page }) => {
    const token = 'e2e-search-debounce-token';

    await seedTokenInLocalStorage(page, token);

    // Initial load returns both tasks
    let callCount = 0;
    await page.route(`**${API_BASE}/tasks**`, async (route) => {
      if (route.request().method() === 'GET') {
        callCount += 1;
        const url = route.request().url();
        if (url.includes('q=groceries')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [GROCERY_TASK] }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [GROCERY_TASK, REPORT_TASK] }),
          });
        }
      } else {
        await route.continue();
      }
    });

    await page.goto(`${BASE_URL}/tasks`);

    // Wait for both tasks to be visible initially
    await expect(page.getByTestId('task-list')).toBeVisible({ timeout: 5000 });

    // Type into the search input
    const searchInput = page.getByTestId('search-input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('groceries');

    // After the debounce delay (300 ms) the filtered list should be shown
    await expect(page.getByTestId('task-list')).toBeVisible({ timeout: 2000 });
    const taskTitles = await page.getByTestId('task-title').allTextContents();
    expect(taskTitles.some((t) => t.includes('Buy groceries'))).toBe(true);
    expect(taskTitles.some((t) => t.includes('Write report'))).toBe(false);
  });

  test('clicking the clear icon empties the search input and reloads all tasks', async ({
    page,
  }) => {
    const token = 'e2e-search-clear-token';

    await seedTokenInLocalStorage(page, token);

    await page.route(`**${API_BASE}/tasks**`, async (route) => {
      if (route.request().method() === 'GET') {
        const url = route.request().url();
        if (url.includes('q=report')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [REPORT_TASK] }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [GROCERY_TASK, REPORT_TASK] }),
          });
        }
      } else {
        await route.continue();
      }
    });

    await page.goto(`${BASE_URL}/tasks`);
    await expect(page.getByTestId('task-list')).toBeVisible({ timeout: 5000 });

    // Type to trigger a filtered search
    const searchInput = page.getByTestId('search-input');
    await searchInput.fill('report');

    // Wait for filtered results
    await page.waitForTimeout(400); // let debounce fire

    // Click the clear icon
    await page.getByTestId('clear-search').click();

    // Search input must be empty
    await expect(searchInput).toHaveValue('');

    // Full task list must reload — both tasks are visible again
    await expect(page.getByTestId('task-list')).toBeVisible({ timeout: 5000 });
    const taskTitles = await page.getByTestId('task-title').allTextContents();
    expect(taskTitles.some((t) => t.includes('Buy groceries'))).toBe(true);
    expect(taskTitles.some((t) => t.includes('Write report'))).toBe(true);
  });

  test('searching for a keyword with no matching tasks shows the no-results empty state', async ({
    page,
  }) => {
    const token = 'e2e-search-empty-state-token';

    await seedTokenInLocalStorage(page, token);

    await page.route(`**${API_BASE}/tasks**`, async (route) => {
      if (route.request().method() === 'GET') {
        const url = route.request().url();
        if (url.includes('q=')) {
          // Any keyword search returns no results
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [] }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [GROCERY_TASK] }),
          });
        }
      } else {
        await route.continue();
      }
    });

    await page.goto(`${BASE_URL}/tasks`);
    await expect(page.getByTestId('task-list')).toBeVisible({ timeout: 5000 });

    const searchInput = page.getByTestId('search-input');
    await searchInput.fill('xyzzy_no_match');

    // Wait for debounce and response
    await page.waitForTimeout(500);

    // The search-specific empty state must be shown
    const emptyState = page.getByTestId('empty-state');
    await expect(emptyState).toBeVisible({ timeout: 2000 });
    await expect(emptyState).toContainText("No results for 'xyzzy_no_match'");

    // The default empty state message must not appear
    await expect(emptyState).not.toContainText('No tasks yet');
  });

  test('typing a keyword while a status filter is active sends both parameters', async ({
    page,
  }) => {
    const token = 'e2e-search-with-filter-token';
    const capturedUrls: string[] = [];

    await seedTokenInLocalStorage(page, token);

    await page.route(`**${API_BASE}/tasks**`, async (route) => {
      if (route.request().method() === 'GET') {
        capturedUrls.push(route.request().url());
        const url = route.request().url();
        if (url.includes('status=pending') && url.includes('q=buy')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [PENDING_TASK] }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ tasks: [GROCERY_TASK, REPORT_TASK, PENDING_TASK] }),
          });
        }
      } else {
        await route.continue();
      }
    });

    await page.goto(`${BASE_URL}/tasks`);
    await expect(page.getByTestId('task-list')).toBeVisible({ timeout: 5000 });

    // Activate the Pending filter
    await page.getByTestId('filter-pending').click();
    await page.waitForTimeout(200);

    // Type a keyword while the Pending filter is active
    const searchInput = page.getByTestId('search-input');
    await searchInput.fill('buy');

    // Wait for debounce to fire
    await page.waitForTimeout(500);

    // At least one of the captured URLs must contain both status=pending and q=buy
    const combinedFilterRequest = capturedUrls.some(
      (url) => url.includes('status=pending') && url.includes('q=buy'),
    );
    expect(combinedFilterRequest).toBe(true);
  });

  test('changing the status filter while a search term is active keeps the search term', async ({
    page,
  }) => {
    const token = 'e2e-search-filter-change-token';
    const capturedUrls: string[] = [];

    await seedTokenInLocalStorage(page, token);

    await page.route(`**${API_BASE}/tasks**`, async (route) => {
      if (route.request().method() === 'GET') {
        capturedUrls.push(route.request().url());
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ tasks: [GROCERY_TASK] }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto(`${BASE_URL}/tasks`);
    await expect(page.getByTestId('task-list')).toBeVisible({ timeout: 5000 });

    // Type a keyword to set a search term
    const searchInput = page.getByTestId('search-input');
    await searchInput.fill('groceries');
    await page.waitForTimeout(500); // let debounce fire

    // Now change the status filter — search term must not be reset
    await page.getByTestId('filter-completed').click();
    await page.waitForTimeout(200);

    // The search input must still contain the original term
    await expect(searchInput).toHaveValue('groceries');

    // The request triggered by the filter change must include the search term
    const filterChangeRequest = capturedUrls.some(
      (url) => url.includes('status=completed') && url.includes('q=groceries'),
    );
    expect(filterChangeRequest).toBe(true);
  });
});
