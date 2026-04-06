import { test, expect, Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BASE_URL = 'http://localhost:4200';
const API_BASE = '/api/v1';
const AUTH_TOKEN_KEY = 'auth_token';

async function mockRegister(page: Page, token = 'e2e-jwt-register-token'): Promise<void> {
  await page.route(`**${API_BASE}/auth/register`, async (route) => {
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ access_token: token, token_type: 'bearer' }),
    });
  });
}

async function mockLogin(page: Page, token = 'e2e-jwt-login-token'): Promise<void> {
  await page.route(`**${API_BASE}/auth/login`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access_token: token, token_type: 'bearer' }),
    });
  });
}

async function mockTaskList(page: Page, tasks: object[] = []): Promise<void> {
  await page.route(`**${API_BASE}/tasks`, async (route) => {
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

async function mockCreateTask(page: Page, task: object): Promise<void> {
  await page.route(`**${API_BASE}/tasks`, async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(task),
      });
    } else {
      await route.continue();
    }
  });
}

async function mockToggleTask(page: Page, taskId: string, updatedTask: object): Promise<void> {
  await page.route(`**${API_BASE}/tasks/${taskId}/toggle`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(updatedTask),
    });
  });
}

async function mockDeleteTask(page: Page, taskId: string): Promise<void> {
  await page.route(`**${API_BASE}/tasks/${taskId}`, async (route) => {
    if (route.request().method() === 'DELETE') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Task deleted' }),
      });
    } else {
      await route.continue();
    }
  });
}

async function seedTokenInLocalStorage(page: Page, token: string): Promise<void> {
  await page.addInitScript(
    ({ key, value }: { key: string; value: string }) => {
      localStorage.setItem(key, value);
    },
    { key: AUTH_TOKEN_KEY, value: token }
  );
}

// ---------------------------------------------------------------------------
// Test suites
// ---------------------------------------------------------------------------

test.describe('Unauthenticated access', () => {
  test('navigating to /tasks without a token redirects to /login', async ({ page }) => {
    // Ensure no token is present in localStorage
    await page.goto(`${BASE_URL}/tasks`);

    await expect(page).toHaveURL(/\/login/);
  });

  test('the login page is accessible without a token', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
  });
});

test.describe('Full user journey', () => {
  const TASK_ID = 'aaaaaaaa-0000-0000-0000-000000000001';
  const NEW_TASK = {
    id: TASK_ID,
    userId: 'user-uuid-1',
    title: 'Buy groceries',
    completed: false,
  };

  test('register → tasks page: after successful registration user is on /tasks', async ({ page }) => {
    const registerToken = 'e2e-register-token';
    await mockRegister(page, registerToken);
    await mockTaskList(page, []);

    await page.goto(`${BASE_URL}/register`);
    await page.fill('input[type="email"]', 'newuser@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/tasks/);
  });

  test('login → tasks page: after successful login user is on /tasks', async ({ page }) => {
    const loginToken = 'e2e-login-token';
    await mockLogin(page, loginToken);
    await mockTaskList(page, []);

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', 'user@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/tasks/);
  });

  test('create task: after login, a created task appears in the task list', async ({ page }) => {
    const loginToken = 'e2e-create-task-token';
    await mockLogin(page, loginToken);

    // Set up route handling: GET returns list with NEW_TASK, POST returns NEW_TASK
    await page.route(`**${API_BASE}/tasks`, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ tasks: [NEW_TASK] }),
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(NEW_TASK),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', 'user@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/tasks/);

    // The task list component loads tasks on init — wait for the task to appear
    const taskTitle = page.getByTestId('task-title').first();
    await expect(taskTitle).toBeVisible({ timeout: 5000 });
    await expect(taskTitle).toHaveText('Buy groceries');
  });

  test('toggle completion: clicking toggle changes task state', async ({ page }) => {
    const loginToken = 'e2e-toggle-token';
    const toggledTask = { ...NEW_TASK, completed: true };

    await mockLogin(page, loginToken);
    await mockTaskList(page, [NEW_TASK]);
    await mockToggleTask(page, TASK_ID, toggledTask);

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', 'user@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/tasks/);

    // Wait for the task to appear
    const toggleBtn = page.getByTestId('toggle-completion').first();
    await expect(toggleBtn).toBeVisible({ timeout: 5000 });

    // Initially pending task has "Complete" button text
    await expect(toggleBtn).toHaveText('Complete');

    await toggleBtn.click();

    // After toggle, the button should say "Reopen"
    await expect(toggleBtn).toHaveText('Reopen');
  });

  test('delete task: clicking delete removes the task from the list', async ({ page }) => {
    const loginToken = 'e2e-delete-token';

    await mockLogin(page, loginToken);

    // First GET returns list with the task
    let taskListCallCount = 0;
    await page.route(`**${API_BASE}/tasks`, async (route) => {
      if (route.request().method() === 'GET') {
        taskListCallCount += 1;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ tasks: taskListCallCount === 1 ? [NEW_TASK] : [] }),
        });
      } else {
        await route.continue();
      }
    });

    await mockDeleteTask(page, TASK_ID);

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', 'user@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/tasks/);

    const deleteBtn = page.getByTestId('delete-button').first();
    await expect(deleteBtn).toBeVisible({ timeout: 5000 });

    await deleteBtn.click();

    // Optimistic removal: task should no longer appear in the list
    await expect(page.getByTestId('task-item')).toHaveCount(0);
  });
});

test.describe('Session persistence', () => {
  const PERSISTED_TASK = {
    id: 'bbbbbbbb-0000-0000-0000-000000000001',
    userId: 'user-uuid-2',
    title: 'Persistent task',
    completed: false,
  };

  test('navigating to /tasks with a valid token in localStorage shows tasks without redirect', async ({
    page,
  }) => {
    const token = 'e2e-persistent-token';

    await seedTokenInLocalStorage(page, token);
    await mockTaskList(page, [PERSISTED_TASK]);

    await page.goto(`${BASE_URL}/tasks`);

    // Should remain on /tasks (not redirected to /login)
    await expect(page).toHaveURL(/\/tasks/);

    const taskTitle = page.getByTestId('task-title').first();
    await expect(taskTitle).toBeVisible({ timeout: 5000 });
    await expect(taskTitle).toHaveText('Persistent task');
  });

  test('tasks remain accessible after a page reload when token is in localStorage', async ({
    page,
  }) => {
    const token = 'e2e-reload-token';

    await seedTokenInLocalStorage(page, token);
    await mockTaskList(page, [PERSISTED_TASK]);

    await page.goto(`${BASE_URL}/tasks`);
    await expect(page).toHaveURL(/\/tasks/);

    // Reload the page
    await page.reload();

    // Should still be on /tasks after reload
    await expect(page).toHaveURL(/\/tasks/);

    const taskTitle = page.getByTestId('task-title').first();
    await expect(taskTitle).toBeVisible({ timeout: 5000 });
    await expect(taskTitle).toHaveText('Persistent task');
  });

  test('localStorage token persists across page navigation', async ({ page }) => {
    const token = 'e2e-nav-token';

    await seedTokenInLocalStorage(page, token);
    await mockTaskList(page, [PERSISTED_TASK]);

    await page.goto(`${BASE_URL}/tasks`);
    await expect(page).toHaveURL(/\/tasks/);

    // Verify the token is still in localStorage after navigation
    const storedToken = await page.evaluate(
      (key: string) => localStorage.getItem(key),
      AUTH_TOKEN_KEY
    );
    expect(storedToken).toBe(token);
  });
});
